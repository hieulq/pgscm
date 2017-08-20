from flask_wtf import FlaskForm
from wtforms import IntegerField, DateField, StringField, SelectField, \
    HiddenField, validators, SubmitField

from pgscm import const as c
from pgscm.utils import __, Select, Submit, Date

data_required = validators.DataRequired(message=__('Required field!'))


class CertificateForm(FlaskForm):
    certificate_code = StringField(
        __('Certificate code'), validators=[data_required],
        render_kw={"placeholder": __('Certificate code')})
    group_area = IntegerField(
        __('Group area'), validators=[data_required],
        render_kw={"placeholder": __('Group area')})
    member_count = IntegerField(
        __('Member count'), validators=[data_required],
        render_kw={"placeholder": __('Member count')})
    certificate_start_date = DateField(
        __('Certificate start date'), widget=Date(),
        render_kw={"placeholder": __('Certificate start date')})
    gov_certificate_id = StringField(
        __('Decision code'),
        validators=[data_required],
        render_kw={"placeholder": __('Decision code')})
    certificate_expiry_date = DateField(
        __('Certificate expiry date'), widget=Date(),
        render_kw={"placeholder": __('Certificate expiry date')})
    status = SelectField(
        __('Status'), validators=[data_required], coerce=int, widget=Select(),
        choices=[(c.CertificateStatusType.approved.value, __('Approved')),
                 (c.CertificateStatusType.rejected.value, __('Rejected')),
                 (c.CertificateStatusType.approved_no_cert.value,
                  __('Approved no cert')),
                 (c.CertificateStatusType.in_conversion.value,
                  __('In conversion'))])
    re_verify_status = SelectField(
        __('Reverify Status'), validators=[data_required], coerce=int,
        widget=Select(),
        choices=[(c.CertificateReVerifyStatusType.not_check.value,
                  __('Not check')),
                 (c.CertificateReVerifyStatusType.decline.value,
                  __('Decline')),
                 (c.CertificateReVerifyStatusType.punish.value, __('Punish')),
                 (c.CertificateReVerifyStatusType.valid.value, __('Valid')),
                 (c.CertificateReVerifyStatusType.warning.value,
                  __('Warning'))])
    owner_farmer_id = SelectField(__('Certificated farmer'), validators=[
        data_required], coerce=str, widget=Select(), id='load_now-farmer')
    owner_group_id = SelectField(__('Certificated group'), validators=[
        data_required], coerce=str, widget=Select(), id='load_now-group')
    id = HiddenField(__('Id'), validators=[data_required])
    submit = SubmitField(__('Submit'), widget=Submit())
