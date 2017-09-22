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


def _check_user_province(manager, kwargs, is_and=False, is_delete=True,
                         is_province=True, is_get_all=False):
    if is_get_all:
        func = manager.instances
    elif len(kwargs['where']) == 0 or is_and:
        func = manager.paginated_instances
    else:
        func = manager.paginated_instances_or
    province_id = current_user.province_id
    if is_region_role() and province_id and is_province:
        kwargs['where'] += \
            (manager.filters['province_id'][None].convert(
                province_id),)
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
        roles = fields.Inline('role')
        province = fields.Inline('province')
        province_id = fields.String()
        last_login_at = fields.DateTimeString()
        current_login_at = fields.DateTimeString()

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_delete=False)
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

    def _filter_group_farmer_on_province(self, kwargs):
        province_id = current_user.province_id
        if province_id and is_region_role():
            gs = [g.id for g in models.Group.query.filter_by(
                province_id=province_id, _deleted_at=None).all()]
            fs = [f.id for f in models.Farmer.query.join(models.Group).filter(
                models.Group.province_id == province_id,
                models.Group._deleted_at == None,
                models.Farmer._deleted_at == None).all()]
            group_filter_exist = False
            farmer_filter_exist = False
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
                        (self.manager.filters['owner_group_id']['in'].convert(
                            {'$in': gs}),)
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
                        (self.manager.filters['owner_farmer_id']['in'].convert(
                            {'$in': fs}),)
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
        day = (datetime.datetime.today() + datetime.timedelta(days=60)) \
            .strftime('%Y-%m-%d')
        func = _check_user_province(self.manager, kwargs, is_province=False,
                                    is_delete=True, is_and=True)
        kwargs['where'] += \
            (self.manager.filters['certificate_expiry_date']['lte'].
             convert({'$lte': day}),
             self.manager.filters['certificate_expiry_date']['gte'].
             convert({'$gte': today}))
        self._filter_group_farmer_on_province(kwargs)
        return func(**kwargs)

    @Route.GET('/total', rel="", schema=Instances(),
               response_schema=Instances())
    def total(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_delete=True,
                                    is_get_all=True)
        del kwargs['per_page']
        del kwargs['page']
        return func(**kwargs)

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        self._filter_group_farmer_on_province(kwargs)
        kwargs['filter_or_cols'] = ['certificate_expiry_date']
        return self.manager.paginated_instances_or(**kwargs)

    @Route.GET('/groups/deleted', schema=Instances(),
               response_schema=Instances())
    def get_cer_for_groups_deleted(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_delete=False,
                                    is_get_all=True)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        kwargs['where'] += (self.manager.filters['owner_group_id']['ne']
                            .convert({'$ne': ''}),)
        del kwargs['per_page']
        del kwargs['page']
        return func(**kwargs)

    @Route.GET('/farmers/deleted', schema=Instances(),
               response_schema=Instances())
    def get_cer_for_farmers_deleted(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_delete=False,
                                    is_get_all=True)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        kwargs['where'] += (self.manager.filters['owner_farmer_id']['ne']
                            .convert({'$ne': ''}),)
        del kwargs['per_page']
        del kwargs['page']
        return func(**kwargs)


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

    def add_filter_province_id(self, kwargs, province_id, is_get_all=False):
        if is_get_all:
            gs = [g.id for g in models.Group.query.filter_by(
                province_id=province_id).all()]
        else:
            gs = [g.id for g in models.Group.query.filter_by(
                province_id=province_id, _deleted_at=None).all()]
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
        return kwargs

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        province_id = current_user.province_id
        func = _check_user_province(self.manager, kwargs, is_province=False)
        if province_id and is_region_role():
            self.add_filter_province_id(kwargs, province_id, False)
        if len(kwargs['where']) == 0:
            gs = [g.id for g in models.Group.query.filter_by(
                province_id=province_id, _deleted_at=None).all()]
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
        province_id = current_user.province_id
        func = _check_user_province(self.manager, kwargs, is_delete=False,
                                    is_province=False)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        if province_id and is_region_role():
            # TODO: function add query province id for /deleted api not work
            self.add_filter_province_id(kwargs, province_id, True)

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
        _deleted_at = fields.DateString()
        _deleted_at._schema = c.DATETIME_SCHEMA

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        func = _check_user_province(self.manager, kwargs)
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
    def get_groups_deleted(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_delete=False,
                                    is_get_all=True)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        del kwargs['per_page']
        del kwargs['page']
        return func(**kwargs)


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

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        func = _check_user_province(self.manager, kwargs)
        return func(**kwargs)

    @Route.GET('/agroup_summary')
    def agroup_summary(self, id: fields.String()) -> fields.String():
        agroup_id = id
        province_id = current_user.province_id
        if province_id and is_region_role():
            gs = [g.id for g in models.Group.query.filter_by(
                province_id=province_id, _deleted_at=None,
                associate_group_id=agroup_id).all()]
        else:
            gs = [g.id for g in models.Group.query.filter_by(
                _deleted_at=None, associate_group_id=agroup_id).all()]
        response = {
            'total_of_gr': len(gs),
            'total_of_farmer': 0,
            'total_of_cert': 0,
            'total_of_area': 0,
            'total_of_approved_area': 0
        }
        for g in gs:
            cs = models.Certificate.query.filter_by(
                    owner_group_id=g, _deleted_at=None).all()
            response['total_of_cert'] += len(cs)
            for cert in cs:
                if cert.status != c.CertificateStatusType.in_conversion:
                    response['total_of_area'] += cert.group_area
                if cert.status == c.CertificateStatusType.approved \
                    or cert.status == c.CertificateStatusType.approved_no_cert:
                    response['total_of_approved_area'] += cert.group_area

            fs = models.Farmer.query.filter_by(
                group_id=g, _deleted_at=None).all()
            response['total_of_farmer'] += len(fs)
        r = json.dumps(response)
        type(r)
        return json.dumps(response)

    @Route.GET('/area')
    def area(self) -> fields.String():
        approved = request.args.get('approved')
        if approved == 'True' or approved == 'true':
            approved = True
        else:
            approved = False
        province_id = current_user.province_id
        if province_id and is_region_role():
            gs = [g.id for g in models.Group.query.filter_by(
                province_id=province_id, _deleted_at=None).all()]
        else:
            gs = [g.id for g in models.Group.query.filter_by(
                _deleted_at=None).all()]
        sum = 0
        for g in gs:
            cs = models.Certificate.query.filter_by(
                owner_group_id=g, _deleted_at=None).all()
            for cert in cs:
                if not approved:
                    sum += cert.group_area
                elif cert.status == c.CertificateStatusType.approved or cert.\
                        status == c.CertificateStatusType.approved_no_cert:
                    sum += cert.group_area
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
        func = _check_user_province(self.manager, kwargs, is_delete=False,
                                    is_get_all=True)
        kwargs['where'] += \
            (self.manager.filters['_deleted_at']['ne'].convert({'$ne': None}),)
        del kwargs['per_page']
        del kwargs['page']
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
