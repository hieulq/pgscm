from flask_potion import ModelResource
from flask_security import current_user
from flask_potion.routes import Route
from flask_potion import fields
from flask_potion.instances import Instances

import datetime

from pgscm.db import models


def _check_user_province(manager, kwargs, is_and=False, is_delete=True,
                         is_province=True):
    if len(kwargs['where']) == 0 or is_and:
        func = manager.paginated_instances
    else:
        func = manager.paginated_instances_or
    province_id = current_user.province_id
    if province_id and is_province:
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
        owner_group_id = fields.String()

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
        return func(**kwargs)

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_province=False,
                                    is_delete=False)
        return func(**kwargs)


class FarmerResource(ModelResource):
    class Meta:
        model = models.Farmer
        id_field_class = fields.String
        include_id = True

    class Schema:
        group = fields.Inline('group')

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        func = _check_user_province(self.manager, kwargs, is_province=False)
        return func(**kwargs)

    @Route.GET('/select2', schema=Instances(),
               response_schema=Instances())
    def select2_api(self, **kwargs):
        kwargs['where'] += \
            (self.manager.filters['_deleted_at'][None].convert(None),)
        del kwargs['per_page']
        del kwargs['page']
        return self.manager.instances(**kwargs)


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


class AssociateGroupResource(ModelResource):
    class Meta:
        model = models.AssociateGroup
        id_field_class = fields.String
        include_id = True

    class Schema:
        province = fields.Inline('province')
        province_id = fields.String()

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
