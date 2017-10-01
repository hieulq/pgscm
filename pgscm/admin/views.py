from flask import render_template, current_app, request, \
    flash, redirect, url_for, jsonify
from flask_security import roles_accepted, current_user, \
    utils as security_utils
import uuid

from . import admin
from .forms import UserForm
from .forms import data_required, match_pass

from pgscm import sqla, user_datastore
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __, DeleteForm, check_role, is_region_role

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
    form.roles.choices = [(r.name, r.description) for r in
                          models.Role.query.order_by(
                              models.Role.name.asc()).all()]

    if current_app.config['AJAX_CALL_ENABLED']:
        form.province_id.choices = []
        province_id = current_user.province_id
        if province_id and is_region_role():
            us = models.User.query.filter_by(
                province_id=province_id).all()
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.filter_by(province_id=province_id).all()]
        return render_template('admin/user.html', form=form, dform=dform)
    else:
        province_id = current_user.province_id
        if province_id and is_region_role():
            us = models.User.query.filter_by(
                province_id=province_id).all()
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.filter_by(province_id=province_id).all()]
        else:
            us = models.User.query.all()
            form.province_id.choices = []

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
                setattr(form.password, 'validators', [data_required,
                                                      match_pass])
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
                del_user = user_datastore.find_user(id=dform.id.data)
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


@admin.route('/vi/quan-tri/vung', endpoint='regions_vi')
@admin.route('/en/admin/regions', endpoint='regions_en')
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def regions():
    return render_template('admin/regions_management.html')


@admin.route('/vi/them-nguoi-dung', endpoint='add_user_vi', methods=['POST'])
@admin.route('/en/add-user', endpoint='add_user_en', methods=['POST'])
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def add_user():
    form = UserForm()
    form.roles.choices = [(r.name, r.description) for r in
                models.Role.query.order_by(models.Role.name.asc()).all()]
    form.province_id.choices = [(form.province_id.data,
                                 form.province_id.label.text)]
    setattr(form.password, 'validators', [data_required, match_pass])
    setattr(form.confirm, 'validators', [data_required])
    form.id.data = str(uuid.uuid4())
    if form.validate_on_submit():
        if not user_datastore.find_user(email=form.email.data):
            province = models.Province.query.filter_by(
                province_id=form.province_id.data).one()
            user_datastore.create_user(
                id=form.id.data, email=form.email.data,
                fullname=form.fullname.data, province=province,
                password=security_utils.hash_password(form.password.data))
            sqla.session.commit()
            for role in form.roles.data:
                user_datastore.add_role_to_user(
                    form.email.data, role)
            sqla.session.commit()
            return jsonify(is_success=True,
                           message=str(__('Add user success!')))
        else:
            form.email.errors.append(
                __('The email was existed!'))
            return jsonify(is_success=False,
                           message=str(__('The email was existed!')))
    else:
        return jsonify(is_success=False,
                       message=str(__('The form is not validate!')))


@admin.route('/vi/sua-nguoi-dung', endpoint='edit_user_vi', methods=['PUT'])
@admin.route('/en/edit-user', endpoint='edit_user_en', methods=['PUT'])
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def edit_user():
    form = UserForm()
    form.roles.choices = [(r.name, r.description) for r in
                          models.Role.query.order_by(
                              models.Role.name.asc()).all()]
    form.province_id.choices = [(form.province_id.data,
                                 form.province_id.label.text)]
    setattr(form.password, 'validators', [match_pass])
    setattr(form.confirm, 'validators', [])
    if form.validate_on_submit():
        edit_user = user_datastore.find_user(id=form.id.data)
        if form.old_password.data:
            if not security_utils.verify_and_update_password(
                    form.old_password.data, edit_user):
                return jsonify(is_success=False,
                               message=str(__('Old password is wrong!')))
            else:
                edit_user.password = security_utils.hash_password(
                    form.password.data)
        temp_user = sqla.session.query(models.User) \
            .filter_by(email=form.email.data).all()
        if not check_user_email(temp_user, edit_user.email):
            form.email.errors.append(__('The email was existed!'))
            return jsonify(is_success=False,
                           message=str(__('The email was existed!')))
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
            return jsonify(is_success=True,
                           message=str(__('Update user success!')))
    else:
        return jsonify(is_success=False,
                       message=str(__('The form is not validate!')))


@admin.route('/vi/xoa-nguoi-dung', endpoint='delete_user_vi',
             methods=['DELETE'])
@admin.route('/en/delete-user', endpoint='delete_user_en', methods=['DELETE'])
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def delete_user():
    dform = DeleteForm()
    if dform.validate_on_submit():
        del_user = user_datastore.find_user(id=dform.id.data)
        user_datastore.delete_user(del_user)
        sqla.session.commit()
        return jsonify(is_success=True,
                       message=str(__('Delete user success!')))
    else:
        return jsonify(is_success=False,
                       message=str(__('The form is not validate!')))
