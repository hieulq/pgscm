from flask import render_template, current_app
from . import admin
from flask_security import roles_required


@admin.route('/')
@roles_required('national_admin')
def index():
    return render_template('admin/index.html')


@admin.route('/users')
@roles_required('national_admin')
def users():
    return render_template('admin/index.html')


@admin.route('/configs')
@roles_required('national_admin')
def configs():
    return render_template('admin/index.html')


@admin.route('/regions')
@roles_required('national_admin')
def regions():
    return render_template('admin/regions_management.html')
