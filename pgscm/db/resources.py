from flask_potion import ModelResource
from flask_security import current_user
from flask_potion.routes import Route
from flask_potion import fields, filters
from flask import request

from pgscm.utils import Instances, is_region_role
from pgscm import const as c


import datetime
import json

from pgscm.db import models


def check_user_associate_group(manager, kwargs, is_and=False, is_delete=True,
                         is_agroup_id=True, is_get_all=False):
    if is_get_all:
        func = manager.instances
    elif len(kwargs['where']) == 0 or is_and:
        func = manager.paginated_instances
    else:
        func = manager.paginated_instances_or
    associate_group_id = current_user.associate_group_id
    if is_region_role() and associate_group_id and is_agroup_id:
        kwargs['where'] += \
            (manager.filters['id'][None].convert(
                associate_group_id),)
    if is_delete:
        kwargs['where'] += \
            (manager.filters['_deleted_at'][None].convert(None),)
    return func


class RoleResource(ModelResource):
    class Meta:
        model = models.Role
        id_field_class = fields.String
        include_id = True


class UserResource(ModelResource):

    class Meta:
        model = models.User
        id_field_class = fields.String
        include_id = True
        exclude_fields = ['password']

    class Schema:
        roles = fields.ToMany('role')
        associate_group = fields.Inline('associate_group')
        associate_group_id = fields.String()
        last_login_at = fields.DateTimeString()
        current_login_at = fields.DateTimeString()

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        associate_group_id = current_user.associate_group_id
        if is_region_role() and associate_group_id:
            kwargs['where'] += \
                (self.manager.filters['associate_group_id'][None].convert(
                    associate_group_id),)
            kwargs['filter_and_cols'] = ['associate_group_id']
        else:
            text_search = request.args.get('text_search')
            if text_search and text_search != 'false':
                agroups_id = [
                    ag.id for ag in models.AssociateGroup.query.filter(
                        models.AssociateGroup.name.contains(
                            text_search)).all()]
                kwargs['where'] += \
                    (self.manager.filters['associate_group_id']['in'].convert(
                        {'$in': agroups_id}),)
                kwargs['filter_and_cols'] = ['associate_group_id']
        func = check_user_associate_group(self.manager,
                                          kwargs, is_delete=False,
                                          is_agroup_id=False)
        return func(**kwargs)


class CertResource(ModelResource):

    class Meta:
        model = models.Certificate
        id_field_class = fields.String
        include_id = True

    class Schema:
        owner_group = fields.Inline('group')
        owner_farmer = fields.Inline('farmer')
        certificate_start_date = fields.DateString()
        certificate_expiry_date = fields.DateString()
        certificate_expiry_date._schema = c.DATETIME_SCHEMA
        certificate_start_date._schema = c.DATETIME_SCHEMA
        owner_group_id = fields.String()
        owner_farmer_id = fields.String()
        _deleted_at = fields.DateString()
        _deleted_at._schema = c.DATETIME_SCHEMA

    def _filter_group_farmer_on_associate_group(self, kwargs,
                    is_cert_for_group=False, is_cert_for_farmer=False):
        associate_group_id = current_user.associate_group_id
        if associate_group_id and is_region_role():
            kwargs['filter_and_cols'] = ['associate_group_id']
            gs = [g.id for g in models.Group.query.filter_by(
                associate_group_id=associate_group_id, _deleted_at=None).all()]
            fs = [f.id for f in models.Farmer.query.join(models.Group).filter(
                models.Group.associate_group_id == associate_group_id,
                models.Group._deleted_at == None,
                models.Farmer._deleted_at == None).all()]
            group_filter_exist = False
            farmer_filter_exist = False
            if is_cert_for_group:
                kwargs['where'] += \
                    (self.manager.filters['owner_group_id']['in'].convert(
                        {'$in': gs}),)
            elif is_cert_for_farmer:
                kwargs['where'] += \
                    (self.manager.filters['owner_farmer_id']['in'].convert(
                        {'$in': fs}),)
            else:
                for cond in kwargs['where']:
                    if cond.attribute == 'owner_group_id' and isinstance(
                            cond.filter, filters.InFilter):
                        value = []
                        for val in cond.value:
                            if val in gs:
                                value.append(val)
                        cond.value = value
                    elif not group_filter_exist:
                        kwargs['where'] += \
                            (self.manager.filters['owner_group_id']['in']
                                 .convert({'$in': gs}),)
                        group_filter_exist = True

                    if cond.attribute == 'owner_farmer_id' and isinstance(
                        cond.filter, filters.InFilter):
                        value = []
                        for val in cond.value:
                            if val in fs:
                                value.append(val)
                        cond.value = value
                    elif not farmer_filter_exist:
                        kwargs['where'] += \
                            (self.manager.filters['owner_farmer_id']['in']
                                 .convert({'$in': fs}),)
                        farmer_filter_exist = True
            if len(kwargs['where']) == 0:
                kwargs['where'] += \
                    (self.manager.filters['owner_group_id']['in'].convert(
                        {'$in': gs}),)
                kwargs['where'] += \
                    (self.manager.filters['owner_farmer_id']['in'].convert(
                        {'$in': fs}),)

    @Route.GET('/nearly_expired', rel="", schema=Instances(),
               response_schema=Instances())
    def nearly_expired(self, **kwargs):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        day = (datetime.datetime.today() + datetime.timedelta(days=45)) \
            .strftime('%Y-%m-%d')
        kwargs['where'] += \
            (self.manager.filters['certificate_expiry_date']['lte'].
             convert({'$lte': day}),
             self.manager.filters['certificate_expiry_date']['gte'].
             convert({'$gte': today}))
        self._filter_group_farmer_on_associate_group(kwargs)
        if 'filter_and_cols' in kwargs:
            kwargs['filter_and_cols'] += ['certificate_expiry_date']
        else:
            kwargs['filter_and_cols'] = ['certificate_expiry_date']
        kwargs['filter_or_cols'] = ['owner_group_id', 'owner_farmer_id']
        func = check_user_associate_group(self.manager, kwargs,
                                          is_agroup_id=False, is_delete=True)
        return func(**kwargs)

    @Route.GET('/total', rel="", schema=Instances(),
               response_schema=Instances())
    def total(self, **kwargs):
        func = check_user_associate_group(self.manager, kwargs, is_delete=True,
                                    is_get_all=True)
        del kwargs['per_page']
        del kwargs['page']
        return func(**kwargs)

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        self._filter_group_farmer_on_associate_group(kwargs)
        kwargs['filter_or_cols'] = ['certificate_expiry_date']
        return self.manager.paginated_instances_or(**kwargs)

    @Route.GET('/groups', schema=Instances(),
               response_schema=Instances())
    def get_cer_for_groups(self, **kwargs):
        self._filter_group_farmer_on_associate_group(kwargs,
                                                     is_cert_for_group=True)
        if len(kwargs['where']) == 1:
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            kwargs['where'] += \
                (self.manager.filters['certificate_expiry_date']['gte'].
                 convert({'$gte': today}),
                 self.manager.filters['certificate_expiry_date']['eq']
                 .convert({'$eq': None}),
                 )
        kwargs['filter_or_cols'] = ['certificate_expiry_date']
        kwargs['filter_and_cols'] = ['owner_group_id']
        kwargs['where'] += (self.manager.filters['owner_group_id']['ne']
                            .convert({'$ne': ''}),)
        return self.manager.paginated_instances_or(**kwargs)

    @Route.GET('/farmers', schema=Instances(),
               response_schema=Instances())
    def get_cer_for_farmers(self, **kwargs):
        self._filter_group_farmer_on_associate_group(kwargs,
                                                     is_cert_for_farmer=True)
        if len(kwargs['where']) == 1:
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            kwargs['where'] += \
                (self.manager.filters['certificate_expiry_date']['gte'].
                 convert({'$gte': today}),
                 self.manager.filters['certificate_expiry_date']['eq']
                 .convert({'$eq': None}),
                 )
        kwargs['filter_or_cols'] = ['certificate_expiry_date']
        kwargs['filter_and_cols'] = ['owner_farmer_id']
        kwargs['where'] += (self.manager.filters['owner_farmer_id']['ne']
                            .convert({'$ne': ''}),)
        return self.manager.paginated_instances_or(**kwargs)

    @Route.GET('/groups/deleted', schema=Instances(),
               response_schema=Instances())
    def get_cer_for_groups_deleted(self, **kwargs):
        self._filter_group_farmer_on_associate_group(kwargs,
                                                     is_cert_for_group=True)
        kwargs['filter_or_cols'] = ['certificate_expiry_date']
        kwargs['filter_and_cols'] = ['owner_group_id']
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        kwargs['where'] += (self.manager.filters['owner_group_id']['ne']
                            .convert({'$ne': ''}),)
        return self.manager.paginated_instances_or(**kwargs)

    @Route.GET('/farmers/deleted', schema=Instances(),
               response_schema=Instances())
    def get_cer_for_farmers_deleted(self, **kwargs):
        self._filter_group_farmer_on_associate_group(kwargs,
                                                     is_cert_for_farmer=True)
        kwargs['filter_or_cols'] = ['certificate_expiry_date']
        kwargs['filter_and_cols'] = ['owner_farmer_id']
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        kwargs['where'] += (self.manager.filters['owner_farmer_id']['ne']
                            .convert({'$ne': ''}),)
        return self.manager.paginated_instances_or(**kwargs)


class FarmerResource(ModelResource):
    class Meta:
        model = models.Farmer
        id_field_class = fields.String
        include_id = True

    class Schema:
        group = fields.Inline('group')
        group_id = fields.String()
        _deleted_at = fields.DateString()
        _deleted_at._schema = c.DATETIME_SCHEMA

    def add_filter_associate_group_id(self, kwargs):
        associate_group_id = current_user.associate_group_id
        if associate_group_id and is_region_role():
            gs = [g.id for g in models.Group.query.filter_by(
                    associate_group_id=associate_group_id,
                    _deleted_at=None).all()]
            for cond in kwargs['where']:
                if cond.attribute == 'group_id' and isinstance(
                        cond.filter, filters.InFilter):
                    value = []
                    for val in cond.value:
                        if val in gs:
                            value.append(val)
                    cond.value = value

            kwargs['where'] += \
                (self.manager.filters['group_id']['in'].convert(
                            {'$in': gs}),)
            kwargs['filter_and_cols'] = ['group_id']
        else:
            text_search = request.args.get('text_search')
            if text_search and text_search != 'false':
                groups_id = [g.id for g in models.Group.query.filter(
                    models.Group.name.contains(text_search)).all()]
                kwargs['where'] += \
                    (self.manager.filters['group_id']['in'].convert(
                        {'$in': groups_id}),)
        return kwargs

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        associate_group_id = current_user.associate_group_id
        self.add_filter_associate_group_id(kwargs)
        func = check_user_associate_group(self.manager,
                                          kwargs, is_agroup_id=False)
        if len(kwargs['where']) == 0 and associate_group_id:
            gs = [g.id for g in models.Group.query.filter_by(
                associate_group_id=associate_group_id, _deleted_at=None).all()]
            kwargs['where'] += \
                (self.manager.filters['group_id']['in'].convert(
                    {'$in': gs}),)
        return func(**kwargs)

    @Route.GET('/select2', schema=Instances(),
               response_schema=Instances())
    def select2_api(self, **kwargs):
        kwargs['where'] += \
            (self.manager.filters['_deleted_at'][None].convert(None),)
        del kwargs['per_page']
        del kwargs['page']
        return self.manager.instances(**kwargs)

    @Route.GET('/deleted', schema=Instances(),
               response_schema=Instances())
    def get_farmers_deleted(self, **kwargs):
        self.add_filter_associate_group_id(kwargs)
        func = check_user_associate_group(self.manager, kwargs,
                                          is_delete=False, is_agroup_id=False)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        return func(**kwargs)


class GroupResource(ModelResource):
    class Meta:
        model = models.Group
        id_field_class = fields.String
        include_id = True

    class Schema:
        province = fields.Inline('province')
        ward = fields.Inline('ward')
        district = fields.Inline('district')
        associate_group = fields.Inline('associate_group')
        province_id = fields.String()
        associate_group_id = fields.String()
        district_id = fields.String()
        ward_id = fields.String()
        _deleted_at = fields.DateString()
        _deleted_at._schema = c.DATETIME_SCHEMA

    def add_agroup_id_filter(self, kwargs):
        associate_group_id = current_user.associate_group_id
        if is_region_role() and associate_group_id:
            kwargs['where'] += \
                (self.manager.filters['associate_group_id'][None].convert(
                    associate_group_id),)
            kwargs['filter_and_cols'] = ['associate_group_id']
        text_search = request.args.get('text_search')
        if text_search and text_search != 'false':
            provinces_id = [
                p.province_id for p in models.Province.query.filter(
                    models.Province.name.contains(text_search)).all()]
            kwargs['where'] += \
                (self.manager.filters['province_id']['in'].convert(
                    {'$in': provinces_id}),)
            districts_id = [
                d.district_id for d in models.District.query.filter(
                    models.District.name.contains(text_search)).all()]
            kwargs['where'] += \
                (self.manager.filters['district_id']['in'].convert(
                    {'$in': districts_id}),)
            wards_id = [p.ward_id for p in models.Ward.query.filter(
                models.Ward.name.contains(text_search)).all()]
            kwargs['where'] += \
                (self.manager.filters['ward_id']['in'].convert(
                    {'$in': wards_id}),)
            if not is_region_role() or not associate_group_id:
                agroups_id = [p.id for p in models.AssociateGroup.query.filter(
                    models.AssociateGroup.name.contains(text_search)).all()]
                kwargs['where'] += \
                    (self.manager.filters['associate_group_id']['in'].convert(
                        {'$in': agroups_id}),)

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        self.add_agroup_id_filter(kwargs)
        func = check_user_associate_group(self.manager,
                                          kwargs, is_agroup_id=False)
        return func(**kwargs)

    @Route.GET('/select2', schema=Instances(),
               response_schema=Instances())
    def select2_api(self, **kwargs):
        kwargs['where'] += \
            (self.manager.filters['_deleted_at'][None].convert(None),)
        associate_group_id = current_user.associate_group_id
        if is_region_role() and associate_group_id:
            kwargs['where'] += \
                (self.manager.filters['associate_group_id'][None].convert(
                    associate_group_id),)
        del kwargs['per_page']
        del kwargs['page']
        return self.manager.instances(**kwargs)

    @Route.GET('/deleted', schema=Instances(),
               response_schema=Instances())
    def get_groups_deleted(self, **kwargs):
        self.add_agroup_id_filter(kwargs)
        func = check_user_associate_group(self.manager, kwargs,
                                          is_delete=False, is_agroup_id=False)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        return func(**kwargs)

    @Route.GET('/group_summary')
    def group_summary(self, id: fields.String()) -> fields.String():
        total_farmer = models.Farmer.query\
            .filter_by(group_id=id, _deleted_at=None).all()
        total_male = models.Farmer.query\
            .filter_by(group_id=id, _deleted_at=None, gender=1).all()
        response = {
            'total_of_farmer': len(total_farmer),
            'total_of_male': len(total_male),
            'total_of_female': len(total_farmer) - len(total_male)
        }
        return json.dumps(response)


class AssociateGroupResource(ModelResource):
    class Meta:
        model = models.AssociateGroup
        id_field_class = fields.String
        include_id = True

    class Schema:
        province = fields.Inline('province')
        id = fields.String()
        province_id = fields.String()
        _deleted_at = fields.DateString()
        _deleted_at._schema = c.DATETIME_SCHEMA

    def add_search_in_province(self, kwargs):
        text_search = request.args.get('text_search')
        if text_search and text_search != 'false':
            provinces_id = [
                p.province_id for p in models.Province.query.filter(
                    models.Province.name.contains(text_search)).all()]
            kwargs['where'] += \
                (self.manager.filters['province_id']['in'].convert(
                    {'$in': provinces_id}),)

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        self.add_search_in_province(kwargs)
        func = check_user_associate_group(self.manager, kwargs)
        return func(**kwargs)

    @Route.GET('/agroup_summary')
    def agroup_summary(self, id: fields.String(),
                       year: fields.Integer()) -> fields.String():
        agroup_id = id
        report_year = year
        current_year = datetime.datetime.now().year
        gs = [g.id for g in models.Group.query.filter_by(
                _deleted_at=None, associate_group_id=agroup_id).all()]
        response = {
            'total_of_gr': len(gs),
            'total_of_farmer': 0,
            'total_of_male': 0,
            'total_of_female': 0,
            'total_of_cert': 0,
            'total_of_area': 0,
            'total_of_approved_area': 0
        }
        for g in gs:
            if current_year == report_year:
                cs = models.Certificate.query.filter_by(
                        owner_group_id=g, _deleted_at=None).all()
            else:
                start_time = datetime.datetime(report_year, 1, 1)\
                    .strftime('%Y-%m-%d')
                end_time = datetime.datetime(report_year, 12, 30)\
                    .strftime('%Y-%m-%d')
                cs = models.Certificate.query.filter(
                    models.Certificate.owner_group_id == g,
                    models.Certificate.certificate_start_date >= start_time,
                    models.Certificate.certificate_start_date <= end_time)\
                    .all()
            response['total_of_cert'] += len(cs)
            for cert in cs:
                if cert.re_verify_status != \
                        c.CertificateReVerifyStatusType.fortuity:
                    response['total_of_area'] += cert.group_area
                if cert.re_verify_status == \
                        c.CertificateReVerifyStatusType.adding or \
                        cert.re_verify_status == \
                        c.CertificateReVerifyStatusType.keeping:
                    response['total_of_approved_area'] += cert.group_area

            fs = models.Farmer.query.filter_by(
                group_id=g, _deleted_at=None).all()
            males = models.Farmer.query.filter_by(
                group_id=g, _deleted_at=None, gender=1).all()
            response['total_of_farmer'] += len(fs)
            response['total_of_male'] += len(males)
        response['total_of_female'] = \
            response['total_of_farmer'] - response['total_of_male']
        return json.dumps(response)

    @Route.GET('/area')
    def area(self) -> fields.String():
        approved = request.args.get('approved')
        if approved == 'True' or approved == 'true':
            approved = True
        else:
            approved = False
        associate_group_id = current_user.associate_group_id
        if associate_group_id and is_region_role():
            gs = [g.id for g in models.Group.query.filter_by(
                associate_group_id=associate_group_id, _deleted_at=None).all()]
        else:
            gs = [g.id for g in models.Group.query.filter_by(
                _deleted_at=None).all()]
        sum = 0
        for g in gs:
            cs = models.Certificate.query.filter_by(
                owner_group_id=g, _deleted_at=None).all()
            for cert in cs:
                if not approved and cert.re_verify_status != \
                        c.CertificateReVerifyStatusType.fortuity:
                    sum += cert.group_area
                elif cert.re_verify_status == \
                        c.CertificateReVerifyStatusType.adding or \
                        cert.re_verify_status == \
                        c.CertificateReVerifyStatusType.keeping:
                    sum += cert.group_area
        return sum

    @Route.GET('/gender')
    def gender(self) -> fields.String():
        gender = int(request.args.get('type'))
        associate_group_id = current_user.associate_group_id
        if associate_group_id and is_region_role():
            gs = [g.id for g in models.Group.query.filter_by(
                associate_group_id=associate_group_id, _deleted_at=None).all()]
        else:
            gs = [g.id for g in models.Group.query.filter_by(
                _deleted_at=None).all()]
        sum = 0
        for g in gs:
            count = models.Farmer.query.filter_by(
                group_id=g, _deleted_at=None, gender=gender).all()
            sum += len(count)
        return sum

    @Route.GET('/select2', schema=Instances(),
               response_schema=Instances())
    def select2_api(self, **kwargs):
        kwargs['where'] += \
            (self.manager.filters['_deleted_at'][None].convert(None),)
        del kwargs['per_page']
        del kwargs['page']
        return self.manager.instances(**kwargs)

    @Route.GET('/deleted', schema=Instances(),
               response_schema=Instances())
    def get_agroups_deleted(self, **kwargs):
        func = check_user_associate_group(self.manager, kwargs,
                                          is_delete=False, is_agroup_id=True)
        self.add_search_in_province(kwargs)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        return func(**kwargs)


class WardResource(ModelResource):
    class Meta:
        model = models.Ward
        id_field_class = fields.String
        include_id = True

    class Schema:
        district = fields.ToOne('district')


class DistrictResource(ModelResource):
    class Meta:
        model = models.District
        id_field_class = fields.String
        include_id = True

    class Schema:
        province = fields.ToOne('province')


class ProvinceResource(ModelResource):
    class Meta:
        model = models.Province
        id_field_class = fields.String
        include_id = True

    @Route.GET('/select2', schema=Instances(),
               response_schema=Instances())
    def select2_api(self, **kwargs):
        del kwargs['per_page']
        del kwargs['page']
        return self.manager.instances(**kwargs)


def init_resources(api):
    api.add_resource(RoleResource)
    api.add_resource(UserResource)
    api.add_resource(CertResource)
    api.add_resource(FarmerResource)
    api.add_resource(GroupResource)
    api.add_resource(AssociateGroupResource)
    api.add_resource(ProvinceResource)
    api.add_resource(DistrictResource)
    api.add_resource(WardResource)
