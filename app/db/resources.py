from flask_potion import ModelResource
from app.db import models


class RoleResource(ModelResource):
    class Meta:
        model = models.Role


class UserResource(ModelResource):
    class Meta:
        model = models.User


def init_resources(api):
    api.add_resource(RoleResource)
    api.add_resource(UserResource)
