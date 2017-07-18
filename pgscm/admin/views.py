from flask import render_template
from . import admin
from flask_security import roles_accepted


@admin.route('/vi/quan-tri', endpoint='index_vi')
@admin.route('/en/admin', endpoint='index_en')
@roles_accepted('national_admin', 'regional_admin')
def index():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/nguoi-dung', endpoint='users_vi')
@admin.route('/en/admin/users', endpoint='users_en')
@roles_accepted('national_admin', 'regional_admin')
def users():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/cau-hinh', endpoint='configs_vi')
@admin.route('/en/admin/configs', endpoint='configs_en')
@roles_accepted('national_admin', 'regional_admin')
def configs():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/vung', endpoint='regions_vi')
@admin.route('/en/admin/regions', endpoint='regions_en')
@roles_accepted('national_admin', 'regional_admin')
def regions():
    return render_template('admin/regions_management.html')
