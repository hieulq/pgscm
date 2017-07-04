from flask_potion import ModelResource
from app.models import models


class UserResource(ModelResource):
    class Meta:
        model = models.User


def init_resources(api):
    api.add_resource(UserResource)
