from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user
from sqlalchemy import func

from . import farmer
from .forms import FarmerForm

from pgscm import sqla
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __, DeleteForm


@farmer.route('/vi/nong-dan', endpoint='index_vi', methods=['GET', 'POST'])
@farmer.route('/en/farmer', endpoint='index_en', methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    form = FarmerForm()
    dform = DeleteForm()
    if current_app.config['AJAX_CALL_ENABLED']:
        return render_template('farmer/index.html', form=form, dform=dform)
    else:
        province_id = current_user.province_id
        form.gender.choices = [(c.GenderType.male.value, __('Male')),
                               (c.GenderType.female.value, __('Female'))]
        form.type.choices = [(c.FarmerType.member.value, __('Member')),
                             (c.FarmerType.reviewer.value, __('Reviewer'))]
        if province_id:
            farmers = models.Farmer.query.filter(
                models.Farmer._deleted_at.is_(None)).join(
                models.Group.query.filter_by(province_id=province_id).all())

            form.group_id.choices = [(p.id, p.name) for p in
                                     models.Group.query.filter_by(
                                         province_id=province_id).all()]
        else:
            farmers = models.Farmer.query.filter(
                models.Farmer._deleted_at.is_(None)).all()
            form.group_id.choices = [(p.id, p.name) for p in
                                     models.Group.query.order_by(
                                         models.Group.name.asc()).all()]

        if request.method == 'POST' and form.data['submit'] \
                and form.validate_on_submit():
            # edit user
            if form.id.data:
                edit_farmer = sqla.session.query(models.Farmer) \
                    .filter_by(id=form.id.data).one()
                edit_farmer.farmer_code = form.farmer_code.data
                edit_farmer.name = form.name.data
                edit_farmer.gender = form.gender.data
                edit_farmer.type = form.type.data
                if edit_farmer.group_id != form.group_id.data:
                    new_group = models.Group.query.filter_by(
                        id=form.group_id.data).one()
                    edit_farmer.group = new_group
                sqla.session.commit()
                for fm in farmers:
                    if fm.id == edit_farmer.id:
                        farmers.remove(fm)
                        farmers.append(edit_farmer)
                flash('Update farmer success!', 'info')

            # add user
            else:
                group_farmer = models.Group.query.filter_by(
                    id=form.group_id.data).one()
                new_farmer = models.Farmer(farmer_code=form.farmer_code.data,
                                           name=form.name.data,
                                           group=group_farmer,
                                           gender=form.gender.data,
                                           type=form.type.data)
                sqla.session.add(new_farmer)
                sqla.session.commit()
                farmers.append(new_farmer)
                flash('Add farmer success!', 'info')

            return redirect(url_for(request.endpoint))

        if request.method == 'POST' and dform.data['submit_del'] \
                and dform.validate_on_submit():
            del_farmer = sqla.session.query(models.Farmer) \
                .filter_by(id=dform.id.data).one()
            del_farmer._deleted_at = func.now()
            if dform.modify_info.data:
                del_farmer._modify_info = dform.modify_info.data
            sqla.session.commit()
            farmers.remove(del_farmer)
            flash('Delete farmer success!', 'info')

            return redirect(url_for(request.endpoint))

        return render_template('farmer/index.html', farmers=farmers,
                               form=form, dform=dform)
