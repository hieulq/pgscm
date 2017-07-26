from flask import render_template, current_app
from flask_security import roles_accepted, current_user

from . import farmer
from .forms import FarmerForm

from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __


@farmer.route('/vi/nong-dan', endpoint='index_vi')
@farmer.route('/en/farmer', endpoint='index_en')
@roles_accepted(*c.ALL_ROLES)
def index():
    if current_app.config['AJAX_CALL_ENABLED']:
        return render_template('farmer/index.html')
    else:
        province_id = current_user.province_id
        form = FarmerForm()
        form.gender.choices = [(c.GenderType.male, __('Male')),
                               (c.GenderType.female, __('Female'))]
        form.type.choices = [(c.FarmerType.member, __('Member')),
                             (c.FarmerType.reviewer, __('Reviewer'))]
        if province_id:
            farmers = models.Farmer.query.join(models.Group).filter(
                models.Group.query.filter_by(province_id=province_id).all())

            form.group.choices = [(p.id, p.name) for p in
                                  models.Group.query.filter_by(
                                      province_id=province_id).all()]
        else:
            farmers = models.Farmer.query.all()
            form.group.choices = [(p.id, p.name) for p in
                                  models.Group.query.order_by(
                                      models.Group.name.asc()).all()]

        return render_template('farmer/index.html', farmers=farmers,
                               genderType=c.GenderType, form=form,
                               farmerType=c.FarmerType)
