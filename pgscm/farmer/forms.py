from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, \
    validators, SubmitField

from pgscm.utils import __, Select

data_required = validators.DataRequired(message=__('Required field!'))


class FarmerForm(FlaskForm):
    farmer_code = StringField(__('Farmer code'), validators=[data_required],
                              render_kw={"placeholder": __('Farmer code')})
    name = StringField(__('Name'), validators=[data_required],
                       render_kw={"placeholder": __('Name')})
    gender = SelectField(__('Gender'), validators=[data_required],
                         coerce=int, widget=Select())
    type = SelectField(__('Type'), validators=[data_required],
                       coerce=int, widget=Select())
    group_id = SelectField(__('Group'), validators=[data_required],
                           coerce=str, widget=Select())
    id = HiddenField(__('Id'))
    submit = SubmitField(__('Submit'), id='pgscm_form_submit')
