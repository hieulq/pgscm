import dateutil.parser

from flask import render_template
from . import main


class User(object):
    """
    Example User object.  Based loosely off of Flask-Login's User model.
    """
    full_name = "Hieu LE"
    avatar = "/static/img/user2-160x160.jpg"
    created_at = dateutil.parser.parse("June 30, 2017")


@main.route('/')
def index():
    current_user = User()
    return render_template('index.html', current_user=current_user)
