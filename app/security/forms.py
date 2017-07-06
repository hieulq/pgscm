from flask_security import forms


class RegisterForm(forms.RegisterForm):
    fullname = forms.StringField('Full name')
