from flask_wtf import FlaskForm
from wtforms import IntegerField, DateField, StringField, SelectField, \
    HiddenField, validators

from pgscm import const as c
from pgscm.utils import __, Select

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
        __('Certificate start date'),
        render_kw={"placeholder": __('Certificate start date')})
    gov_certificate_id = StringField(
        __('Decision code'),
        validators=[data_required],
        render_kw={"placeholder": __('Decision code')})
    certificate_expiry_date = DateField(
        __('Certificate expiry date'),
        render_kw={"placeholder": __('Certificate expiry date')})
    status = SelectField(
        __('Status'), validators=[data_required], coerce=str, widget=Select(),
        choices=[(c.CertificateStatusType.approve, __('Approve')),
                 (c.CertificateStatusType.reject, __('Reject')),
                 (c.CertificateStatusType.in_conversion, __('In conversion'))])
    re_verify_status = SelectField(
        __('Reverify Status'), validators=[data_required], coerce=str,
        widget=Select(),
        choices=[(c.CertificateReVerifyStatusType.not_check, __('Not '
                                                                'check')),
                 (c.CertificateReVerifyStatusType.decline, __('Decline')),
                 (c.CertificateReVerifyStatusType.punish, __('Punish')),
                 (c.CertificateReVerifyStatusType.valid, __('Valid')),
                 (c.CertificateReVerifyStatusType.warning, __('Warning'))])
    owner_farmer_id = SelectField(__('Certificated farmer'), validators=[
        data_required], coerce=str, widget=Select())
    owner_group_id = SelectField(__('Certificated group'), validators=[
        data_required], coerce=str, widget=Select())
    id = HiddenField(__('Id'), validators=[data_required])
