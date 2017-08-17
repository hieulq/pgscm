from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators, \
    SubmitField

from pgscm.utils import __, Select, Submit

data_required = validators.DataRequired(message=__('Required field!'))


class GroupForm(FlaskForm):
    group_code = StringField(__('Group code'),
                             validators=[data_required],
                             render_kw={
                                 "placeholder": __(
                                     'Group code')})
    name = StringField(__('Name'), validators=[data_required],
                       render_kw={"placeholder": __('Name')})
    province_id = SelectField(__('Province'), validators=[data_required],
                              coerce=str, widget=Select(),
                              id='load_now-province')
    district_id = SelectField(__('District'), validators=[data_required],
                              coerce=str, widget=Select())
    ward_id = SelectField(__('Ward'), validators=[data_required],
                          coerce=str, widget=Select())
    village = StringField(__('Village'),
                          render_kw={"placeholder": __('Village')})
    associate_group_id = SelectField(__('Associated Group'),
                                     validators=[data_required], coerce=str,
                                     widget=Select(),
                                     id='load_now-associate_group')
    id = HiddenField(__('Id'), validators=[data_required])
    submit = SubmitField(__('Submit'), widget=Submit())
