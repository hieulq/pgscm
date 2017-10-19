from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, \
    validators, SubmitField

from pgscm import const as c
from pgscm.utils import __, Select, Submit

data_required = validators.DataRequired(message=__('Required field!'))


class FarmerForm(FlaskForm):
    farmer_code = StringField(__('Farmer code'), validators=[data_required],
                              render_kw={"placeholder": __('Farmer code')})
    name = StringField(__('Name'), validators=[data_required],
                       render_kw={"placeholder": __('Name')})
    gender = SelectField(__('Gender'), validators=[data_required],
                         coerce=int, widget=Select(),
                         choices=[(c.GenderType.male.value, __('Male')),
                           (c.GenderType.female.value, __('Female'))])
    type = SelectField(__('Type'), validators=[data_required],
                       coerce=int, widget=Select(),
                       choices=[(c.FarmerType.member.value, __('Member')),
                        (c.FarmerType.reviewer.value, __('Reviewer')),
                        (c.FarmerType.leader.value, __('Leader')),
                        (c.FarmerType.deputy_leader.value,
                         __('Deputy leader')),
                        (c.FarmerType.counter.value, __('Counter'))])
    group_id = SelectField(__('Group'), validators=[data_required],
                           coerce=str, widget=Select(), id='load_now-group',
                           choices=[])
    id = HiddenField(__('Id'), validators=[data_required])
    submit = SubmitField(__('Submit'), widget=Submit())
