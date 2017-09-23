import uuid

from flask import render_template, current_app, request, \
    flash, redirect, url_for, jsonify
from flask_security import roles_accepted, current_user
from sqlalchemy import func

from . import farmer
from .forms import FarmerForm

from pgscm import sqla
from pgscm.db import models
from pgscm import const as c
from pgscm.utils import __, DeleteForm, check_role, is_region_role, soft_delete

crud_role = c.ADMIN_MOD_ROLE


@farmer.route('/vi/nong-dan', endpoint='index_vi', methods=['GET', 'POST'])
@farmer.route('/en/farmer', endpoint='index_en', methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    form = FarmerForm()
    dform = DeleteForm()
    form.gender.choices = [(c.GenderType.male.value, __('Male')),
                           (c.GenderType.female.value, __('Female'))]
    form.type.choices = [(c.FarmerType.member.value, __('Member')),
                         (c.FarmerType.reviewer.value, __('Reviewer'))]
    if current_app.config['AJAX_CALL_ENABLED']:
        form.group_id.choices = []
        return render_template('farmer/index.html', form=form, dform=dform)
    else:
        province_id = current_user.province_id
        if province_id and is_region_role():
            farmers = models.Farmer.query.join(models.Group).filter(
                models.Group.province_id == province_id,
                models.Group._deleted_at == None,
                models.Farmer._deleted_at == None).order_by(
                models.Farmer.name.asc()).all()
            form.group_id.choices = [(p.id, p.name) for p in
                                     models.Group.query.filter_by(
                                         province_id=province_id,
                                         _deleted_at=None).order_by(
                                         models.Group.name.asc()).all()]
        else:
            farmers = models.Farmer.query.filter_by(
                _deleted_at=None).all()
            form.group_id.choices = []

        form.group_id.choices = [(form.group_id.data,
                                  form.group_id.label.text)]
        # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            # edit user
            if form.id.data:
                if form.validate_on_submit():
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
                    flash(str(__('Update farmer success!')), 'success')

            # add user
            else:
                form.id.data = str(uuid.uuid4())
                if form.validate_on_submit():
                    group_farmer = models.Group.query.filter_by(
                        id=form.group_id.data).one()
                    new_farmer = models.Farmer(
                        id=form.id.data, type=form.type.data,
                        farmer_code=form.farmer_code.data,
                        name=form.name.data, group=group_farmer,
                        gender=form.gender.data)
                    sqla.session.add(new_farmer)
                    sqla.session.commit()
                    farmers.append(new_farmer)
                    flash(str(__('Add farmer success!')), 'success')

                return redirect(url_for(request.endpoint))

        # form delete submit
        if request.method == 'POST' and dform.data['submit_del']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif dform.validate_on_submit():
                del_farmer = sqla.session.query(models.Farmer) \
                    .filter_by(id=dform.id.data).one()
                del_farmer._deleted_at = func.now()
                if dform.modify_info.data:
                    del_farmer._modify_info = dform.modify_info.data
                sqla.session.commit()
                farmers.remove(del_farmer)
                flash(str(__('Delete farmer success!')), 'success')

                return redirect(url_for(request.endpoint))

        return render_template('farmer/index.html', farmers=farmers,
                               form=form, dform=dform)


@farmer.route('/vi/them-nong-dan', endpoint='add_farmer_vi', methods=['POST'])
@farmer.route('/en/add-farmer', endpoint='add_farmer_en', methods=['POST'])
@roles_accepted(*c.ADMIN_MOD_ROLE)
def add_farmer():
    form = FarmerForm()
    form.group_id.choices = [(form.group_id.data,
                              form.group_id.label.text)]
    form.id.data = str(uuid.uuid4())
    if form.validate_on_submit():
        group_farmer = models.Group.query.filter_by(
            id=form.group_id.data).one()
        new_farmer = models.Farmer(
            id=form.id.data, type=form.type.data,
            farmer_code=form.farmer_code.data,
            name=form.name.data, group=group_farmer,
            gender=form.gender.data)
        sqla.session.add(new_farmer)
        sqla.session.commit()
        return jsonify(is_success=True, message=str(__('Add farmer success!')))
    else:
        return jsonify(is_success=False,
                       message=str(__('The form is not validate!')))


@farmer.route('/vi/sua-nong-dan', endpoint='edit_farmer_vi', methods=['PUT'])
@farmer.route('/en/edit-farmer', endpoint='edit_farmer_en', methods=['PUT'])
@roles_accepted(*c.ADMIN_MOD_ROLE)
def edit_farmer():
    form = FarmerForm()
    form.group_id.choices = [(form.group_id.data,
                              form.group_id.label.text)]
    if form.id.data:
        if form.validate_on_submit():
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
            return jsonify(is_success=True,
                           message=str(__('Update farmer success!')))
        else:
            return jsonify(is_success=False,
                           message=str(__('The form is not validate!')))
    else:
        return jsonify(is_success=False,
                       message=str(__("Can't get id of object edit!")))


@farmer.route('/vi/xoa-nong-dan', endpoint='delete_farmer_vi',
              methods=['DELETE'])
@farmer.route('/en/delete-farmer', endpoint='delete_farmer_en',
              methods=['DELETE'])
@roles_accepted(*c.ADMIN_MOD_ROLE)
def delete_farmer():
    return soft_delete(sqla, models.Farmer)
