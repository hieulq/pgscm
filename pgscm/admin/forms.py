from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, \
    validators, SubmitField, SelectMultipleField, PasswordField
from wtforms.fields.html5 import EmailField

from pgscm.utils import __, Select, Submit, MultiSelect

data_required = validators.DataRequired(message=__('Required field!'))
match_pass = validators.EqualTo('confirm', message=__('Passwords must match'))


class UserForm(FlaskForm):
    fullname = StringField(__('Name'), validators=[data_required],
                           render_kw={"placeholder": __('Name')})
    email = EmailField(__('Email'), validators=[data_required,
                                                validators.Email('')],
                       render_kw={"placeholder": __('Email')})
    old_password = PasswordField(__('Old password'), id='old_pass')
    password = PasswordField(__('New Password'), validators=[data_required,
                                                             match_pass])
    confirm = PasswordField(__('Repeat Password'), validators=[data_required])
    roles = SelectMultipleField(__('Role'), validators=[data_required],
                                widget=MultiSelect())
    associate_group_id = SelectField(__('Associated Group'),
                                     validators=[data_required], coerce=str,
                                     widget=Select(),
                                     id='load_now-associate_group')
    id = HiddenField(__('Id'), validators=[data_required])
    submit = SubmitField(__('Submit'), widget=Submit())
