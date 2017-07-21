from flask_potion import ModelResource
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
