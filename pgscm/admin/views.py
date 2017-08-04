from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user, \
    utils as security_utils
import uuid

from . import admin
from .forms import UserForm

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
    if current_app.config['AJAX_CALL_ENABLED']:
        form.province_id.choices = []
        return render_template('admin/user.html', form=form, dform=dform)
    else:
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
            elif form.validate_on_submit():
                # edit user
                if form.id.data:
                    pass

                # add user
                else:
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
                flash(str(__('The form is not validated!')), 'error')

        # form delete submit
        if request.method == 'POST' and dform.data['submit_del']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif dform.validate_on_submit():
                del_user = user_datastore.find_user(id=form.id.data)
                user_datastore.delete_user(del_user)
                sqla.session.commit()

                flash(str(__('Delete farmer success!')), 'success')
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
