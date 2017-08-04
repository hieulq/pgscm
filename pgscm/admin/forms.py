from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators, \
    DateTimeField, SubmitField

from pgscm.utils import __, Select, Submit

data_required = validators.DataRequired(message=__('Required field!'))


class UserForm(FlaskForm):
    fullname = StringField(__('Name'), validators=[data_required],
                       render_kw={"placeholder": __('Name')})
    email = StringField(__('Email'), validators=[validators.Email],
                        render_kw={"placeholder": __('Email')})
    last_login_ip = StringField(__('Last login IP'))
    current_login_ip = StringField(__('Current login IP'))
    last_login_at = DateTimeField(__('Last login at'))
    current_login_at = DateTimeField(__('Current login at'))
    province_id = SelectField(__('Province'), validators=[data_required],
                              coerce=str, widget=Select())
    id = HiddenField(__('Id'))
    submit = SubmitField(__('Submit'), widget=Submit())
