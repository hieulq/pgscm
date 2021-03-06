from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators, \
    SubmitField, IntegerField

from pgscm.utils import __, Select, Submit

data_required = validators.DataRequired(message=__('Required field!'))


class AssociateGroupForm(FlaskForm):
    associate_group_code = StringField(__('Associate group code'),
                                       validators=[data_required],
                                       render_kw={
                                           "placeholder": __(
                                               'Associate group code')})
    name = StringField(__('Name'), validators=[data_required],
                       render_kw={"placeholder": __('Name')})
    email = StringField(__('Email'), validators=[validators.Email()],
                        render_kw={"placeholder": __('Email')})
    province_id = SelectField(__('Province'),
                              widget=Select(), id='load_now-province')
    created_at = IntegerField(__('Year created'),
                              render_kw={"placeholder": __('Enter year')})
    id = HiddenField(__('Id'), validators=[data_required])
    submit = SubmitField(__('Submit'), widget=Submit())
