from flask_potion import ModelResource
from pgscm.db import models


class RoleResource(ModelResource):
    class Meta:
        model = models.Role


class UserResource(ModelResource):
    class Meta:
        model = models.User


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
    api.add_resource(ProvinceResource)
    api.add_resource(DistrictResource)
    api.add_resource(WardResource)
