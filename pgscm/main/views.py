from flask import render_template, redirect, g

from . import main


@main.route('/vi', endpoint='index_vi')
@main.route('/en', endpoint='index_en')
def index():
    return render_template('index.html')


@main.route('/')
def default():
    return redirect('/' + g.language)
