from flask_security import forms
from pgscm.utils import _l


class RegisterForm(forms.RegisterForm):
    fullname = forms.StringField(_l('Full name'))
