from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user
from sqlalchemy import exc

from . import admin
from .forms import UserForm

from pgscm import sqla
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __, DeleteForm, check_role, email_is_exist


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
            (r.id, r.description) for r in
            models.Role.query.order_by(
                models.Role.name.asc()).all()]

        # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif form.validate_on_submit():
                # edit user
                if form.id.data:
                    edit_user = sqla.session.query(models.User) \
                        .filter_by(id=form.id.data).one()
                    if edit_user.email != form.email.data and \
                            email_is_exist(form.email.data):
                        flash(str(__('Email existed!')), 'error')
                    else:
                        edit_user.email = form.email.data
                        edit_user.fullname = form.fullname.data
                        if form.province_id.data != edit_user.province_id:
                            edit_user.province = models.Province.query\
                                .filter_by(province_id=form.province_id.data)\
                                .one()
                        edit_user.roles = []
                        for role_id in form.roles.data:
                            edit_user.roles.append(models.Role.query.filter_by(
                                id=role_id).one())
                        sqla.session.commit()
                        for user in us:
                            if user.id == edit_user.id:
                                us.remove(user)
                                us.append(edit_user)
                        flash(str(__('Update farmer success!')), 'success')
                        return redirect(url_for(request.endpoint))

                # add user
                else:
                    if email_is_exist(form.email.data):
                        flash(str(__('Email existed!')), 'error')
                    else:
                        roles = []
                        for role_id in form.roles.data:
                            roles.append(models.Role.query.filter_by(
                                id=role_id).one())
                        provice = None
                        if form.province_id.data:
                            provice = models.Province.query.filter_by(
                                province_id=form.province_id.data).one()
                        new_user = models.User(email=form.email.data,
                            fullname=form.fullname.data, roles=roles,
                            province=provice)
                        sqla.session.add(new_user)
                        sqla.session.commit()
                        us.append(new_user)
                        flash(str(__('Add user success!')), 'success')
                        return redirect(url_for(request.endpoint))
            else:
                flash(str(__('The form not validated!')), 'error')

        # form delete submit
        if request.method == 'POST' and dform.data['submit_del']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif dform.validate_on_submit():
                try:
                    del_user = sqla.session.query(models.User) \
                        .filter_by(id=dform.id.data).one()
                    sqla.session.delete(del_user)
                    flash(str(__('Delete farmer success!')), 'success')
                    return redirect(url_for(request.endpoint))
                except exc.SQLAlchemyError:
                    flash(str(__('Can not delete user!')), 'error')

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
