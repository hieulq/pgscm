from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user, \
    utils as security_utils
import uuid

from . import admin
from .forms import UserForm
from .forms import data_required, match_pass

from pgscm import sqla, user_datastore
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __, DeleteForm, check_role

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
        form.province_id.choices = [
            (p.province_id, p.type + " " + p.name) for p in
            models.Province.query.order_by(
                models.Province.name.asc()).all()]
    form.roles.choices = [
        (r.name, r.description) for r in
        models.Role.query.order_by(
            models.Role.name.asc()).all()]

    # form create or edit submit
    if request.method == 'POST' and form.data['submit']:
        if not check_role(crud_role):
            return redirect(url_for(request.endpoint))
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
                if len(temp_user) > 2 or temp_user[0].id != edit_user.id:
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
                        print(old_role.name)
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
            setattr(form.password, 'validators', [data_required])
            setattr(form.confirm, 'validators', [data_required])
            if form.validate_on_submit():
                if not user_datastore.find_user(email=form.email.data):
                    user_datastore.create_user(id=str(uuid.uuid4()),
                        email=form.email.data, fullname=form.fullname.data,
                        password=security_utils.hash_password(
                                                   form.password.data))
                    sqla.session.commit()
                    for role in form.roles.data:
                        user_datastore.add_role_to_user(
                            form.email.data, role)
                    sqla.session.commit()
                    flash(str(__('Add user success!')), 'success')
                    return redirect(url_for(request.endpoint))
                else:
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


@admin.route('/vi/quan-tri/cau-hinh', endpoint='configs_vi')
@admin.route('/en/admin/configs', endpoint='configs_en')
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def configs():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/vung', endpoint='regions_vi')
@admin.route('/en/admin/regions', endpoint='regions_en')
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def regions():
    return render_template('admin/regions_management.html')
