from flask_potion import ModelResource
from flask_security import current_user
from flask_potion.routes import Route
from flask_potion import fields
from flask_potion.instances import Instances


from pgscm.db import models


class RoleResource(ModelResource):
    class Meta:
        model = models.Role
        id_field_class = fields.String


class UserResource(ModelResource):
    class Meta:
        model = models.User
        id_field_class = fields.String


class CertResource(ModelResource):
    class Meta:
        model = models.Certificate
        id_field_class = fields.String


class FarmerResource(ModelResource):
    class Meta:
        model = models.Farmer
        id_field_class = fields.String


class GroupResource(ModelResource):
    class Meta:
        model = models.Group
        id_field_class = fields.String


class AssociateGroupResource(ModelResource):
    class Meta:
        model = models.AssociateGroup
        id_field_class = fields.String
        include_id = True

    class Schema:
        province = fields.Inline('province')

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        province_id = current_user.province_id
        if province_id:
            kwargs['where'] += \
                (self.manager.filters['province'][None].convert(province_id),)
        return self.manager.paginated_instances_or(**kwargs)


class WardResource(ModelResource):
    class Meta:
        model = models.Ward
        id_field_class = fields.String


class DistrictResource(ModelResource):
    class Meta:
        model = models.District
        id_field_class = fields.String


class ProvinceResource(ModelResource):
    class Meta:
        model = models.Province
        id_field_class = fields.String


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
