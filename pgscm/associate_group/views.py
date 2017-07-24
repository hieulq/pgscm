from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import agroup
from .forms import AssociateGroupForm

from pgscm.db import models
from pgscm import const as c


@agroup.route('/vi/lien-nhom', endpoint='index_vi')
@agroup.route('/en/associate-group', endpoint='index_en')
@roles_accepted(c.N_ADMIN, c.R_ADMIN, c.R_MOD, c.N_MOD, c.N_USER)
def index():
    if current_app.config['AJAX_CALL_ENABLED']:
        return render_template('agroup/index.html')
    else:
        province_id = current_user.province_id
        form = AssociateGroupForm()
        form.province.choices = [(p.province_id, p.name) for p in
                                 models.Province.query.all()]
        if province_id:
            ags = models.AssociateGroup.query.filter_by(
                province_id=province_id).all()
            choice = [(p, n) for (p, n) in form.province.choices
                      if p == province_id]
            form.province.default = choice[0]
        else:
            ags = models.AssociateGroup.query.all()
        return render_template('agroup/index.html', ags=ags,
                               form=form)
