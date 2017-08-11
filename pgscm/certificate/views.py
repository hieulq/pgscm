from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user
from sqlalchemy import func

from . import certificate

from .forms import CertificateForm, data_required
from pgscm import sqla
from pgscm.db import models
from pgscm.utils import __, DeleteForm, check_role
from pgscm import const as c

crud_role = c.ADMIN_MOD_ROLE


@certificate.route('/vi/chung-chi', endpoint='index_vi',
                   methods=['GET', 'POST'])
@certificate.route('/en/certificates', endpoint='index_en',
                   methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    form = CertificateForm()
    dform = DeleteForm()

    if current_app.config['AJAX_CALL_ENABLED']:
        form.owner_farmer_id.choices = []
        form.owner_group_id.choices = []
        return render_template('certificate/index.html', form=form,
                               dform=dform)
    else:
        province_id = current_user.province_id
        if province_id:
            cs = models.Certificate.query.join(models.Group).filter(
                models.Group.province_id == province_id,
                models.Group._deleted_at == None,
                models.Certificate._deleted_at == None).all()
            form.owner_farmer_id.choices = [
                (f.id, f.name) for f in
                models.Farmer.query.join(models.Group).filter(
                    models.Group.province_id == province_id,
                    models.Group._deleted_at == None,
                    models.Farmer._deleted_at == None).order_by(
                    models.Farmer.name.asc()).all()]
            form.owner_group_id.choices = [
                (g.id, g.name) for g in
                models.Group.query.filter_by(
                    province_id=province_id,
                    _deleted_at=None).order_by(
                    models.Group.name.asc()).all()]
        else:
            cs = models.Certificate.query.filter_by(_deleted_at=None).all()
            form.owner_farmer_id.choices = [
                (f.id, f.name) for f in
                models.Farmer.query.filter_by(
                    _deleted_at=None).order_by(
                    models.Farmer.name.asc()).all()]
            form.owner_group_id.choices = [
                (g.id, g.name) for g in
                models.Group.query.filter_by(
                    _deleted_at=None).order_by(
                    models.Group.name.asc()).all()]

            # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))

            # edit certificate
            if form.id.data:
                setattr(form.id, 'validators', [data_required])
                if form.validate_on_submit():
                    start_date = form.certificate_start_date.data
                    expiry_date = form.certificate_expiry_date.data
                    if start_date > expiry_date:
                        form.certificate_expiry_date.errors.append(
                            __('The expiry date must greater than start date'))
                        flash((str(__('The expiry date must greater than '
                                      'start date!'))), 'error')
                    else:
                        edit_certificate = sqla.session \
                            .query(models.Certificate) \
                            .filter_by(id=form.id.data).one()
                        edit_certificate.certificate_code = form \
                            .certificate_code.data
                        edit_certificate.group_area = form.group_area.data
                        edit_certificate.member_count = form.member_count.data
                        edit_certificate.certificate_start_date = start_date
                        edit_certificate.certificate_expiry_date = expiry_date
                        edit_certificate.gov_certificate_id = form \
                            .gov_certificate_id.data
                        edit_certificate.status = form.status.data
                        edit_certificate.re_verify_status = form \
                            .re_verify_status.data
                        if edit_certificate.owner_farmer_id != \
                                form.owner_farmer_id.data:
                            edit_certificate.owner_farmer = models.Farmer \
                                .query.filter_by(
                                    id=form.owner_farmer_id.data).one()
                        if edit_certificate.owner_group_id != \
                                form.owner_group_id.data:
                            edit_certificate.owner_group = models.Group.query \
                                .filter_by(id=form.owner_group_id.data).one()
                        flash(str(__('Update certificate success!')),
                              'success')
                        return redirect(url_for(request.endpoint))
                else:
                    flash(str(__('The form is not validated!')), 'error')

            # add certificate
            else:
                setattr(form.id, 'validators', [])
                if form.validate_on_submit():
                    start_date = form.certificate_start_date.data
                    expiry_date = form.certificate_expiry_date.data
                    if start_date > expiry_date:
                        form.certificate_expiry_date.errors.append(
                            __('The expiry date must greater than start date'))
                        flash((str(__('The expiry date must greater '
                                      'than start date!'))), 'error')
                    else:
                        owner_farmer = models.Farmer.query \
                            .filter_by(id=form.owner_farmer_id.data).one()
                        owner_group = models.Group.query \
                            .filter_by(id=form.owner_group_id.data).one()
                        new_cert = models.Certificate(
                            certificate_code=form.certificate_code.data,
                            group_area=form.group_area.data,
                            member_count=form.member_count.data,
                            certificate_start_date=start_date,
                            certificate_expiry_date=expiry_date,
                            gov_certificate_id=form.gov_certificate_id.data,
                            status=form.status.data,
                            re_verify_status=form.re_verify_status.data,
                            owner_farmer=owner_farmer, owner_group=owner_group)
                        sqla.session.add(new_cert)
                        sqla.session.commit()
                        flash(str(__('Add certificate success!')), 'success')
                        return redirect(url_for(request.endpoint))
                else:
                    flash(str(__('The form is not validated!')), 'error')

        # form delete submit
        if request.method == 'POST' and dform.data['submit_del']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif dform.validate_on_submit():
                del_cert = sqla.session.query(models.Certificate) \
                    .filter_by(id=dform.id.data).one()
                del_cert._deleted_at = func.now()
                if dform.modify_info.data:
                    del_cert._modify_info = dform.modify_info.data
                sqla.session.commit()
                cs.remove(del_cert)
                flash(str(__('Delete certificate success!')), 'success')
                return redirect(url_for(request.endpoint))

        return render_template('certificate/index.html', cs=cs, form=form,
                               dform=dform)


@certificate.route('/vi/chung-chi/chi-tiet/<string:certificate_id>',
                   endpoint='detail_vi')
@certificate.route('/en/certificates/detail/<string:certificate_id>',
                   endpoint='detail_en')
@roles_accepted(*c.ALL_ROLES)
def detail(certificate_id):
    return render_template('certificate/detail.html')
