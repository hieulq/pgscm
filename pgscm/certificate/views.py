from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import certificate

from .forms import CertificateForm
from pgscm.db import models
from pgscm.utils import DeleteForm
from pgscm import const as c


@certificate.route('/vi/chung-chi', endpoint='index_vi')
@certificate.route('/en/certificates', endpoint='index_en')
@roles_accepted(*c.ALL_ROLES)
def index():
    form = CertificateForm()
    dform = DeleteForm()
    if current_app.config['AJAX_CALL_ENABLED']:
        form.owner_farmer_id.choices = []
        form.owner_group_id.choices = []
        return render_template('certificate/index.html', form=form,
                               dform=dform)
    else:
        province_id = current_user.province_id
        if province_id:
            cs = models.Certificate.query.join(models.Group).filter(
                models.Group.query.filter_by(
                    province_id=province_id.all())).order_by(
                models.Certificate.name.asc()).all()
            form.owner_farmer_id.choices = [
                (f.id, f.name) for f in
                models.Farmer.query.join(models.Group).filter(
                    models.Group.query.filter_by(
                        province_id=province_id.all())).order_by(
                    models.Farmer.name.asc()).all()]
            form.owner_group_id.choices = [
                (g.id, g.name) for g in
                models.Group.query.filter_by(
                    province_id=province_id).all().order_by(
                    models.Group.name.asc())]
        else:
            cs = models.Certificate.query.all()
            form.owner_farmer_id.choices = [
                (f.id, f.name) for f in
                models.Farmer.query.order_by(
                    models.Farmer.name.asc()).all()]
            form.owner_group_id.choices = [
                (g.id, g.name) for g in
                models.Group.query.order_by(
                    models.Group.name.asc()).all()]
        return render_template('certificate/index.html', cs=cs, form=form,
                               dform=dform)


@certificate.route('/vi/chung-chi/chi-tiet/<string:certificate_id>',
                   endpoint='detail_vi')
@certificate.route('/en/certificates/detail/<string:certificate_id>',
                   endpoint='detail_en')
@roles_accepted(*c.ALL_ROLES)
def detail(certificate_id):
    return render_template('certificate/detail.html')
