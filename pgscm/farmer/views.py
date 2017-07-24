from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import farmer

from pgscm.db import models
from pgscm import const as c


@farmer.route('/vi/nong-dan', endpoint='index_vi')
@farmer.route('/en/farmer', endpoint='index_en')
@roles_accepted(c.N_ADMIN, c.R_ADMIN, c.R_MOD, c.N_MOD, c.N_USER)
def index():
    if current_app.config['AJAX_CALL_ENABLED']:
        return render_template('farmer/index.html')
    else:
        province_id = current_user.province_id
        if province_id:
            # groups = models.Group.query.filter_by(
            #     province_id=province_id).all()
            farmers = models.Farmer.query.join(models.Group).filter(models.Group.query.filter_by(
                province_id=province_id).all())
        else:
            farmers = models.Farmer.query.all()
        return render_template('farmer/index.html', farmers=farmers,
                               enabled_action=['edit', 'delete', 'add'])
