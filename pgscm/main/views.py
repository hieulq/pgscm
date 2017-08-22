from flask import render_template, redirect, g
import datetime

from . import main


@main.route('/vi', endpoint='index_vi')
@main.route('/en', endpoint='index_en')
def index():
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    return render_template('index.html', time=today)


@main.route('/')
def default():
    return redirect('/' + g.language)
