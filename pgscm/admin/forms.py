from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, \
    validators, SubmitField, SelectMultipleField
from wtforms.fields.html5 import EmailField

from pgscm.utils import __, Select, Submit, MultiSelect

data_required = validators.DataRequired(message=__('Required field!'))


class UserForm(FlaskForm):
    fullname = StringField(__('Name'), validators=[data_required],
                           render_kw={"placeholder": __('Name')})
    email = EmailField(__('Email'), validators=[data_required,
                                                validators.Email('')],
                       render_kw={"placeholder": __('Email')})
    # roles = SelectField(__('Role'), validators=[data_required],
    #                     coerce=str, widget=Select())
    roles = SelectMultipleField(__('Role'), validators=[data_required],
                                widget=MultiSelect())
    province_id = SelectField(__('Province'), validators=[data_required],
                              coerce=str, widget=Select())
    id = HiddenField(__('Id'))
    submit = SubmitField(__('Submit'), widget=Submit())
