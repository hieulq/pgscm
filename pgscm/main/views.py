from flask import render_template, redirect, g
from flask_security import current_user
import datetime

from pgscm import const as c

from . import main


@main.route('/vi', endpoint='index_vi')
@main.route('/en', endpoint='index_en')
def index():
    if current_user.is_authenticated:
        for role in current_user.roles:
            if role == c.C_USER:
                if g.language == 'vi':
                    group_url = '/vi/nhom'
                else:
                    group_url = '/en/group'
                return redirect(group_url)
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    return render_template('index.html', time=today)


@main.route('/')
def default():
    return redirect('/' + g.language)
