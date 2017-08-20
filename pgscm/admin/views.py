from flask import render_template, request, \
    flash, redirect, url_for, current_app
from flask_security import roles_accepted, current_user, \
    utils as security_utils
import uuid
import datetime
from sqlalchemy import func, or_

from . import admin
from .forms import UserForm
from .forms import data_required, match_pass

from pgscm import sqla, user_datastore
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __, DeleteForm, check_role
from pgscm.certificate.forms import CertificateForm

crud_role = c.ONLY_ADMIN_ROLE


@admin.route('/vi/quan-tri', endpoint='index_vi')
@admin.route('/en/admin', endpoint='index_en')
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def index():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/nguoi-dung', endpoint='users_vi',
             methods=['GET', 'POST'])
@admin.route('/en/admin/users', endpoint='users_en', methods=['GET', 'POST'])
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def users():
    form = UserForm()
    dform = DeleteForm()
    province_id = current_user.province_id
    if province_id:
        us = models.User.query.filter_by(
            province_id=province_id).all()
        form.province_id.choices = [
            (p.province_id, p.type + " " + p.name) for p in
            models.Province.query.filter_by(province_id=province_id).all()]
    else:
        us = models.User.query.all()
        form.province_id.choices = []
        # form.province_id.choices = [
        #     (p.province_id, p.type + " " + p.name) for p in
        #     models.Province.query.order_by(
        #         models.Province.name.asc()).all()]
    form.roles.choices = [
        (r.name, r.description) for r in
        models.Role.query.order_by(
            models.Role.name.asc()).all()]

    # form create or edit submit
    if request.method == 'POST' and form.data['submit']:
        if not check_role(crud_role):
            return redirect(url_for(request.endpoint))
        form.province_id.choices = [(form.province_id.data,
                                     form.province_id.label.text)]
        # edit user
        if form.id.data:
            # remove required validator in fields pass and confirm
            #  when form is edit form
            setattr(form.password, 'validators', [match_pass])
            setattr(form.confirm, 'validators', [])
            if form.validate_on_submit():
                edit_user = user_datastore.find_user(id=form.id.data)
                if form.old_password.data:
                    if not security_utils.verify_and_update_password(
                            form.old_password.data, edit_user):
                        flash(str(__('Old password is wrong!')), 'error')
                        # TODO: fix return to keep current state of form
                        return redirect(url_for(request.endpoint))
                    else:
                        edit_user.password = security_utils.hash_password(
                            form.password.data)
                temp_user = sqla.session.query(models.User) \
                    .filter_by(email=form.email.data).all()
                if not check_user_email(temp_user, edit_user.email):
                    form.email.errors.append(
                        __('The email was existed!'))
                    flash(str(__('The email was existed!')), 'error')
                else:
                    edit_user.email = form.email.data
                    edit_user.fullname = form.fullname.data
                    if form.province_id.data != edit_user.province_id:
                        edit_user.province = models.Province.query \
                            .filter_by(province_id=form.province_id.data) \
                            .one()
                    for new_role in form.roles.data:
                        role_is_added = False
                        for r in edit_user.roles:
                            if new_role == r.name:
                                role_is_added = True
                                break
                        if not role_is_added:
                            user_datastore.add_role_to_user(
                                edit_user.email, new_role)
                    temp_roles = list(edit_user.roles)
                    for old_role in temp_roles:
                        if old_role.name not in form.roles.data:
                            user_datastore.remove_role_from_user(
                                edit_user.email, old_role.name)
                    user_datastore.put(edit_user)
                    for user in us:
                        if user.id == edit_user.id:
                            us.remove(user)
                            us.append(edit_user)
                    flash(str(__('Update user success!')), 'success')
                    return redirect(url_for(request.endpoint))
            else:
                flash(str(__('The form is not validated!')), 'error')

        # add user
        else:
            setattr(form.password, 'validators', [data_required, match_pass])
            setattr(form.confirm, 'validators', [data_required])
            form.id.data = str(uuid.uuid4())
            if form.validate_on_submit():
                if not user_datastore.find_user(email=form.email.data):
                    province = models.Province.query.filter_by(
                        province_id=form.province_id.data).one()
                    user_datastore.create_user(id=form.id.data,
                        email=form.email.data, fullname=form.fullname.data,
                        province=province, password=security_utils
                                        .hash_password(form.password.data))
                    sqla.session.commit()
                    for role in form.roles.data:
                        user_datastore.add_role_to_user(
                            form.email.data, role)
                    sqla.session.commit()
                    flash(str(__('Add user success!')), 'success')
                    return redirect(url_for(request.endpoint))
                else:
                    form.email.errors.append(
                        __('The email was existed!'))
                    flash(str(__('The email was existed!')), 'error')
            else:
                flash(str(__('The form is not validated!')), 'error')

    # form delete submit
    if request.method == 'POST' and dform.data['submit_del']:
        if not check_role(crud_role):
            return redirect(url_for(request.endpoint))
        elif dform.validate_on_submit():
            del_user = user_datastore.find_user(id=form.id.data)
            user_datastore.delete_user(del_user)
            sqla.session.commit()

            flash(str(__('Delete user success!')), 'success')
            return redirect(url_for(request.endpoint))

    return render_template('admin/user.html', us=us,
                           form=form, dform=dform)


# user_list_result: users list from result of query to user with email
#                   in form
def check_user_email(user_list_result, edit_user_email):
    #  email was not register
    if not len(user_list_result):
        return True
    # email is edit user's email
    elif len(user_list_result) == 1 and \
            user_list_result[0].email == edit_user_email:
        return True
    # email was registered
    else:
        return False


@admin.route('/vi/quan-tri/canh-bao', endpoint='alarms_vi')
@admin.route('/en/admin/alarms', endpoint='alarms_en')
@roles_accepted(*c.ADMIN_MOD_ROLE)
def alarms():
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
        if province_id:
            cs = models.Certificate.query.join(models.Group).filter(
                models.Group._deleted_at == None,
                models.Certificate._deleted_at == None,
                or_(models.Certificate.certificate_expiry_date >= today,
                    models.Certificate.certificate_expiry_date == None)
            ).all()
            del form.owner_group_id
            form.owner_farmer_id.choices = [
                (f.id, f.name) for f in
                models.Farmer.query.join(models.Group).filter(
                    models.Group._deleted_at == None,
                    models.Farmer._deleted_at == None).order_by(
                    models.Farmer.name.asc()).all()]
        else:
            cs = models.Certificate.query.filter(
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

        return render_template('admin/alarm.html', cs=cs, form=form,
                               dform=dform)


@admin.route('/vi/quan-tri/vung', endpoint='regions_vi')
@admin.route('/en/admin/regions', endpoint='regions_en')
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def regions():
    return render_template('admin/regions_management.html')
