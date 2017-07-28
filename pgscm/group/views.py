from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import group
from .forms import GroupForm

from pgscm.db import models
from pgscm.utils import DeleteForm
from pgscm import const as c


@group.route('/vi/nhom', endpoint='index_vi')
@group.route('/en/group', endpoint='index_en')
@roles_accepted(*c.ALL_ROLES)
def index():
    form = GroupForm()
    dform = DeleteForm()
    if current_app.config['AJAX_CALL_ENABLED']:
        form.ward_id.choices = []
        form.district_id.choices = []
        form.province_id.choices = []
        return render_template('group/index.html', form=form, dform=dform)
    else:
        province_id = current_user.province_id
        if province_id:
            gs = models.Group.query.filter_by(
                province_id=province_id).all()
            form.associate_group_id.choices = [(
                ag.id, ag.name) for ag in
                models.AssociateGroup.query.filter_by(
                    province_id=province_id).order_by(
                    models.AssociateGroup.name.asc()).all()]
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.filter_by(
                    province_id=province_id).order_by(
                    models.Province.name.asc()).all()]
            form.district_id.choices = [
                (d.district_id, d.type + " " + d.name) for d in
                models.District.query.filter_by(
                    province_id=province_id).order_by(
                    models.District.name.asc()).all()]
            form.ward_id.choices = [
                (w.ward_id, w.type + " " + w.name) for w in
                models.Ward.query.join(models.District).filter(
                    models.District.query.filter_by(
                        province_id=province_id).all()).order_by(
                    models.Ward.name.asc())]
        else:
            gs = models.Group.query.all()
            form.associate_group_id.choices = [(
                ag.id, ag.name) for ag in
                models.AssociateGroup.query.order_by(
                    models.AssociateGroup.name.asc()).all()]
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.order_by(
                    models.Province.name.asc()).all()]
            form.district_id.choices = [
                (d.district_id, d.type + " " + d.name) for d in
                models.District.query.order_by(
                    models.District.name.asc()).all()]
            form.ward_id.choices = [(w.ward_id, w.type + " " + w.name) for w in
                                    models.Ward.query.order_by(
                                        models.Ward.name.asc()).all()]
        return render_template('group/index.html', gs=gs,
                               form=form, dform=dform)
