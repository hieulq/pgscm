from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import agroup
from .forms import AssociateGroupForm

from pgscm.db import models
from pgscm import const as c


@agroup.route('/vi/lien-nhom', endpoint='index_vi')
@agroup.route('/en/associate-group', endpoint='index_en')
@roles_accepted(*c.ALL_ROLES)
def index():
    form = AssociateGroupForm()
    if current_app.config['AJAX_CALL_ENABLED']:
        form.province_id.choices = []
        return render_template('agroup/index.html', form=form)
    else:
        province_id = current_user.province_id
        if province_id:
            ags = models.AssociateGroup.query.filter_by(
                province_id=province_id).all()
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.filter_by(province_id=province_id).all()]
        else:
            ags = models.AssociateGroup.query.all()
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.order_by(
                    models.Province.name.asc()).all()]
        return render_template('agroup/index.html', ags=ags,
                               form=form)
