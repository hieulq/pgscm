from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators

from pgscm.utils import __, Select

data_required = validators.DataRequired(message=__('Required field!'))


class FarmerForm(FlaskForm):
    code = StringField(__('Farmer code'), validators=[data_required])
    name = StringField(__('Name'), validators=[data_required])
    gender = SelectField(__('Gender'), validators=[data_required],
                         coerce=str, widget=Select())
    type = SelectField(__('Type'), validators=[data_required],
                       coerce=str, widget=Select())
    group = SelectField(__('Group'), validators=[data_required],
                        coerce=str, widget=Select())
    id = HiddenField(__('Id'), validators=[data_required])
