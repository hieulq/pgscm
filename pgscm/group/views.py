from flask import render_template
from flask_security import roles_accepted

from . import group

from pgscm import const as c


@group.route('/vi/nhom', endpoint='index_vi')
@group.route('/en/group', endpoint='index_en')
@roles_accepted(c.N_ADMIN, c.N_MOD, c.N_USER)
def index():
    return render_template('group/index.html')
