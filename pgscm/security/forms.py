from flask_security import forms
from wtforms import SelectField, validators

from pgscm.utils import __
from pgscm.db import models


class RegisterForm(forms.RegisterForm):
    fullname = forms.StringField(__('Full name'))
    province_id = SelectField(
        __('Province'),
        validators=[validators.DataRequired(message=__('Required field!'))])

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.province_id.choices = [(p.province_id, p.name) for p in
                                    models.Province.query.order_by(
                                        models.Province.name).all()]


class LoginForm(forms.LoginForm):
    def __init__(self, *args, **kwargs):
        # disable csrf for only login form to enable token auth
        kwargs['meta'] = {}
        kwargs['meta'].setdefault('csrf', False)
        super(LoginForm, self).__init__(*args, **kwargs)
