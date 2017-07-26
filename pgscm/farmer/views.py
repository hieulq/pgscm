from flask import render_template, current_app, request
from flask_security import roles_accepted, current_user

from . import farmer
from .forms import FarmerForm

from pgscm import sqla
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __


@farmer.route('/vi/nong-dan', endpoint='index_vi', methods=['GET', 'POST'])
@farmer.route('/en/farmer', endpoint='index_en', methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    if current_app.config['AJAX_CALL_ENABLED']:
        return render_template('farmer/index.html')
    else:
        province_id = current_user.province_id
        form = FarmerForm()
        form.gender.choices = [(c.GenderType.male.value, __('Male')),
                               (c.GenderType.female.value, __('Female'))]
        form.type.choices = [(c.FarmerType.member.value, __('Member')),
                             (c.FarmerType.reviewer.value, __('Reviewer'))]
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

        if request.method == 'POST' and form.is_submitted():
            group_farmer = models.Group.query.filter_by(
                id=form.group.data).one()
            new_farmer = models.Farmer(farmer_code=form.code.data,
                                       name=form.name.data, group=group_farmer,
                                       gender=form.gender.data,
                                       type=form.type.data)
            sqla.session.add(new_farmer)
            sqla.session.commit()

            # return redirect(url_for('/vi/nong-dan'))

        return render_template('farmer/index.html', farmers=farmers,
                               genderType=c.GenderType, form=form,
                               farmerType=c.FarmerType)
