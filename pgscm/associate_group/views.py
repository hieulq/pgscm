from flask import render_template
from flask_security import roles_accepted

from . import agroup

from pgscm.db import models
from pgscm import const as c


@agroup.route('/vi/lien-nhom', endpoint='index_vi')
@agroup.route('/en/associate-group', endpoint='index_en')
@roles_accepted(c.N_ADMIN, c.N_MOD, c.N_USER)
def index():
    ags = models.AssociateGroup.query.all()
    return render_template('agroup/index.html', ags=ags)
