from flask_security import forms
from pgscm.utils import __


class RegisterForm(forms.RegisterForm):
    fullname = forms.StringField(__('Full name'))
