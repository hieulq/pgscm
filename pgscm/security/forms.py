from flask_security import forms
from pgscm.utils import __


class RegisterForm(forms.RegisterForm):
    fullname = forms.StringField(__('Full name'))


class LoginForm(forms.LoginForm):
    def __init__(self, *args, **kwargs):
        # disable csrf for only login form to enable token auth
        kwargs['csrf_enabled'] = False
        super(LoginForm, self).__init__(*args, **kwargs)
