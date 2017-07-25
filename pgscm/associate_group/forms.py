from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators

from pgscm.utils import __, Select


data_required = validators.DataRequired(message=__('Required field!'))


class AssociateGroupForm(FlaskForm):
    code = StringField(__('Associate group code'), validators=[data_required])
    name = StringField(__('Name'), validators=[data_required])
    email = StringField(__('Email'), validators=[validators.Email])
    province = SelectField(__('Province'), validators=[data_required],
                           coerce=str, widget=Select())
    id = HiddenField(__('Id'), validators=[data_required])
