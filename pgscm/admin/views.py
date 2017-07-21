from flask import render_template
from flask_security import roles_accepted

from . import admin
from pgscm import const as c


@admin.route('/vi/quan-tri', endpoint='index_vi')
@admin.route('/en/admin', endpoint='index_en')
@roles_accepted(c.N_ADMIN, c.R_ADMIN)
def index():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/nguoi-dung', endpoint='users_vi')
@admin.route('/en/admin/users', endpoint='users_en')
@roles_accepted(c.N_ADMIN, c.R_ADMIN)
def users():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/cau-hinh', endpoint='configs_vi')
@admin.route('/en/admin/configs', endpoint='configs_en')
@roles_accepted(c.N_ADMIN, c.R_ADMIN)
def configs():
    return render_template('admin/index.html')


@admin.route('/vi/quan-tri/vung', endpoint='regions_vi')
@admin.route('/en/admin/regions', endpoint='regions_en')
@roles_accepted(c.N_ADMIN, c.R_ADMIN)
def regions():
    return render_template('admin/regions_management.html')
