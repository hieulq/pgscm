from flask_potion import ModelResource
from flask_login import current_user
from flask_potion.routes import Route
from flask_potion.instances import Instances
from flask_potion import fields

from pgscm.db import models


class RoleResource(ModelResource):
    class Meta:
        model = models.Role


class UserResource(ModelResource):
    class Meta:
        model = models.User


class CertResource(ModelResource):
    class Meta:
        model = models.Certificate


class FarmerResource(ModelResource):
    class Meta:
        model = models.Farmer


class GroupResource(ModelResource):
    class Meta:
        model = models.Group


class AssociateGroupResource(ModelResource):
    class Meta:
        model = models.AssociateGroup

    class Schema:
        province = fields.ToOne('province')

    @Route.GET('', rel="instances", schema=Instances(),
               response_schema=Instances())
    def instances(self, **kwargs):
        province_id = current_user.province_id
        if province_id:
            kwargs['where'] += \
                (self.manager.filters['province'][None].convert(province_id),)
        return self.manager.paginated_instances(**kwargs)


class WardResource(ModelResource):
    class Meta:
        model = models.Ward


class DistrictResource(ModelResource):
    class Meta:
        model = models.District


class ProvinceResource(ModelResource):
    class Meta:
        model = models.Province


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
