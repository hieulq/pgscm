from flask import render_template
from . import admin
from app.main.views import User

current_user = User()


@admin.route('/')
def index():
    return render_template('admin/index.html', current_user=current_user)


@admin.route('/users')
def users():
    return render_template('admin/index.html', current_user=current_user)


@admin.route('/configs')
def configs():
    return render_template('admin/index.html', current_user=current_user)
