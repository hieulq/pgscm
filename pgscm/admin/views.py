from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import admin
from .forms import UserForm

from pgscm.db import models
from pgscm.utils import DeleteForm
from pgscm import const as c


@admin.route('/vi/quan-tri', endpoint='index_vi')
@admin.route('/en/admin', endpoint='index_en')
@roles_accepted(*c.ONLY_ADMIN_ROLE)
def index():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/nguoi-dung', endpoint='users_vi')
@admin.route('/en/admin/users', endpoint='users_en')
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
