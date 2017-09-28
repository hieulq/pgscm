import datetime
import uuid

from flask import render_template, current_app, request, \
    flash, redirect, url_for, jsonify
from flask_security import roles_accepted, current_user
from sqlalchemy import func, or_

from . import certificate

from .forms import CertificateForm
from pgscm import sqla
from pgscm.db import models
from pgscm.utils import __, DeleteForm, check_role, is_region_role, soft_delete
from pgscm import const as c

crud_role = c.ADMIN_MOD_ROLE


@certificate.route('/vi/chung-chi', endpoint='index_vi',
                   methods=['GET', 'POST'])
@certificate.route('/en/certificates', endpoint='index_en',
                   methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    return render_template('certificate/index.html')


@certificate.route('/vi/chung-chi-nong-dan', endpoint='farmers_vi',
                   methods=['GET', 'POST'])
@certificate.route('/en/certificates-farmer', endpoint='farmers_en',
                   methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def farmers():
    form = CertificateForm()
    dform = DeleteForm()

    if current_app.config['AJAX_CALL_ENABLED']:
        form.owner_farmer_id.choices = []
        form.owner_group_id.choices = []
        return render_template('certificate/index.html', form=form,
                               dform=dform, only_farmer=True)
    else:
        province_id = current_user.province_id
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        if province_id and is_region_role():
            cs = []
            tmp_cs = models.Certificate.query.join(models.Farmer).filter(
                models.Farmer._deleted_at == None,
                models.Certificate.owner_farmer_id != None,
                models.Certificate._deleted_at == None,
                or_(models.Certificate.certificate_expiry_date >= today,
                    models.Certificate.certificate_expiry_date == None)
            ).all()
            for cert in tmp_cs:
                if cert.owner_farmer.group.province_id == province_id:
                    cs.append(cert)

            del form.owner_group_id
            form.owner_farmer_id.choices = [
                (f.id, f.name) for f in
                models.Farmer.query.join(models.Group).filter(
                    models.Group._deleted_at == None,
                    models.Farmer._deleted_at == None).order_by(
                    models.Farmer.name.asc()).all()]
        else:
            cs = models.Certificate.query.filter(
                models.Certificate.owner_farmer_id != None,
                models.Certificate._deleted_at == None,
                or_(models.Certificate.certificate_expiry_date >= today,
                    models.Certificate.certificate_expiry_date == None)
            ).all()
            form.owner_farmer_id.choices = []
            del form.owner_group_id

            # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))

            form.owner_farmer_id.choices = [(form.owner_farmer_id.data,
                                             form.owner_farmer_id.label.text)]
            form.owner_group_id.choices = [(form.owner_group_id.data,
                                            form.owner_group_id.label.text)]
            # edit certificate
            if form.id.data:
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
                form.id.data = str(uuid.uuid4())
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
                            id=form.id.data,
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
                               dform=dform, only_farmer=True)


@certificate.route('/vi/chung-chi-nhom', endpoint='groups_vi',
                   methods=['GET', 'POST'])
@certificate.route('/en/certificates-group', endpoint='groups_en',
                   methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def groups():
    form = CertificateForm()
    dform = DeleteForm()

    if current_app.config['AJAX_CALL_ENABLED']:
        form.owner_farmer_id.choices = []
        form.owner_group_id.choices = []
        return render_template('certificate/index.html', form=form,
                               dform=dform, only_farmer=False)
    else:
        province_id = current_user.province_id
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        if province_id and is_region_role():
            cs = models.Certificate.query.join(models.Group).filter(
                models.Group._deleted_at == None,
                models.Group.province_id == province_id,
                models.Certificate.owner_group != None,
                models.Certificate._deleted_at == None,
                or_(models.Certificate.certificate_expiry_date >= today,
                    models.Certificate.certificate_expiry_date == None)
            ).all()
            del form.owner_farmer_id
            form.owner_group_id.choices = [
                (g.id, g.name) for g in
                models.Group.query.filter_by(
                    province_id=province_id,
                    _deleted_at=None).order_by(
                    models.Group.name.asc()).all()]
        else:
            cs = models.Certificate.query.filter(
                models.Certificate._deleted_at == None,
                models.Certificate.owner_group != None,
                or_(models.Certificate.certificate_expiry_date >= today,
                    models.Certificate.certificate_expiry_date == None)
            ).all()
            del form.owner_farmer_id
            form.owner_group_id.choices = []

            # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))

            form.owner_farmer_id.choices = [(form.owner_farmer_id.data,
                                             form.owner_farmer_id.label.text)]
            form.owner_group_id.choices = [(form.owner_group_id.data,
                                            form.owner_group_id.label.text)]
            # edit certificate
            if form.id.data:
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
                form.id.data = str(uuid.uuid4())
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
                            id=form.id.data,
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
                               dform=dform, only_farmer=False)


def add_value_for_select_field(form):
    if form.owner_farmer_id.data != 'None':
        del form.owner_group_id
        form.owner_farmer_id.choices = [(form.owner_farmer_id.data,
                                        form.owner_farmer_id.label.text)]
    elif form.owner_group_id.data != 'None':
        del form.owner_farmer_id
        form.owner_group_id.choices = [(form.owner_group_id.data,
                                        form.owner_group_id.label.text)]


@certificate.route('/vi/them-chung-chi', endpoint='add_certificate_vi',
                   methods=['POST'])
@certificate.route('/en/add-certificate', endpoint='add_certificate_en',
                   methods=['POST'])
@roles_accepted(*c.ADMIN_MOD_ROLE)
def add_certificate():
    form = CertificateForm()
    add_value_for_select_field(form)
    form.id.data = str(uuid.uuid4())
    if form.validate_on_submit():
        start_date = form.certificate_start_date.data
        expiry_date = form.certificate_expiry_date.data
        if start_date > expiry_date:
            form.certificate_expiry_date.errors.append(
                __('The expiry date must greater than start date'))
            return jsonify(is_success=False,
                           message=str(__('The expiry date must greater '
                                          'than start date!')))
        else:
            owner_farmer = None
            owner_group = None
            if form.owner_farmer_id:
                owner_farmer = models.Farmer.query \
                    .filter_by(id=form.owner_farmer_id.data).one()
            elif form.owner_group_id:
                owner_group = models.Group.query \
                    .filter_by(id=form.owner_group_id.data).one()
            new_cert = models.Certificate(
                id=form.id.data,
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
            return jsonify(is_success=True, message=str(
                __('Add certificate success!')))
    else:
            return jsonify(is_success=False,
                           message=str(__('The form is not validate!')))


@certificate.route('/vi/sua-chung-chi', endpoint='edit_certificate_vi',
                   methods=['PUT'])
@certificate.route('/en/edit-certificate', endpoint='edit_certificate_en',
                   methods=['PUT'])
@roles_accepted(*c.ADMIN_MOD_ROLE)
def edit_certificate():
    form = CertificateForm()
    add_value_for_select_field(form)
    if form.validate_on_submit():
        if form.validate_on_submit():
            start_date = form.certificate_start_date.data
            expiry_date = form.certificate_expiry_date.data
            if start_date > expiry_date:
                form.certificate_expiry_date.errors.append(
                    __('The expiry date must greater than start date'))
                return jsonify(is_success=False,
                               message=str(__('The expiry date must greater '
                                              'than start date!')))
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
                if form.owner_farmer_id:
                    if edit_certificate.owner_farmer_id != \
                            form.owner_farmer_id.data:
                        edit_certificate.owner_farmer = models.Farmer \
                            .query.filter_by(
                                id=form.owner_farmer_id.data).one()
                elif form.owner_group_id:
                    if edit_certificate.owner_group_id != \
                            form.owner_group_id.data:
                        edit_certificate.owner_group = models.Group.query \
                            .filter_by(id=form.owner_group_id.data).one()
                return jsonify(is_success=True, message=str(
                    __('Edit certificate success!')))
        else:
                return jsonify(is_success=False,
                               message=str(__('The form is not validate!')))


@certificate.route('/vi/xoa-chung-chi', endpoint='delete_certificate_vi',
                   methods=['DELETE'])
@certificate.route('/en/delete-certificate', endpoint='delete_certificate_en',
                   methods=['DELETE'])
@roles_accepted(*c.ADMIN_MOD_ROLE)
def delete_certificate():
    return soft_delete(sqla, "certificate", models)
