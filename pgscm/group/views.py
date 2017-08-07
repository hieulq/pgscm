from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user
from sqlalchemy import func

from . import group
from .forms import GroupForm, data_required

from pgscm import sqla
from pgscm.db import models
from pgscm.utils import __, DeleteForm, check_role
from pgscm import const as c

crud_role = c.ADMIN_MOD_ROLE


@group.route('/vi/nhom', endpoint='index_vi', methods=['GET', 'POST'])
@group.route('/en/group', endpoint='index_en', methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    form = GroupForm()
    dform = DeleteForm()
    if current_app.config['AJAX_CALL_ENABLED']:
        form.associate_group_id.choices = []
        form.ward_id.choices = []
        form.district_id.choices = []
        form.province_id.choices = []
        return render_template('group/index.html', form=form, dform=dform)
    else:
        province_id = current_user.province_id
        if province_id:
            gs = models.Group.query.filter_by(
                province_id=province_id, _deleted_at=None).all()
            # gs = models.Group.query.filter_by(
            #     province_id=province_id).all()
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
            gs = models.Group.query.filter_by(_deleted_at=None).all()
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

        # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            # edit group
            if form.id.data:
                setattr(form.id, 'validators', [data_required])
                if form.validate_on_submit():
                    edit_group = sqla.session.query(models.Group) \
                        .filter_by(id=form.id.data).one()
                    edit_group.group_code = form.group_code.data
                    edit_group.name = form.name.data
                    edit_group.village = form.village.data
                    if edit_group.associate_group_id != \
                            form.associate_group_id.data:
                        edit_group.associate_group = sqla.session\
                            .query(models.AssociateGroup) \
                            .filter_by(id=form.associate_group_id.data).one()
                    if edit_group.province_id != form.province_id.data:
                        edit_group.province = sqla.session\
                            .query(models.Province) \
                            .filter_by(province_id=form.province_id.data).one()
                    if edit_group.district_id != form.district_id.data:
                        edit_group.district = sqla.session\
                            .query(models.District) \
                            .filter_by(district_id=form.district_id.data).one()
                    if edit_group.ward_id != form.ward_id.data:
                        edit_group.ward = sqla.session.query(models.Ward) \
                            .filter_by(ward_id=form.ward_id.data).one()
                    sqla.session.commit()
                    for gr in gs:
                        if gr.id == edit_group.id:
                            gs.remove(gr)
                            gs.append(edit_group)
                    flash(str(__('Update group success!')), 'success')
                    return redirect(url_for(request.endpoint))
                else:
                    flash(str(__('The form is not validated!')), 'error')

            # add group
            else:
                setattr(form.id, 'validators', [])
                if form.validate_on_submit():
                    associate_group = sqla.session.query(
                        models.AssociateGroup) \
                        .filter_by(id=form.associate_group_id.data).one()
                    province = sqla.session.query(models.Province) \
                        .filter_by(province_id=form.province_id.data).one()
                    district = sqla.session.query(models.District) \
                        .filter_by(district_id=form.district_id.data).one()
                    ward = sqla.session.query(models.Ward) \
                        .filter_by(ward_id=form.ward_id.data).one()
                    new_group = models.Group(group_code=form.group_code.data,
                                             name=form.name.data,
                                             village=form.village.data,
                                             ward=ward, district=district,
                                             associate_group=associate_group,
                                             province=province)
                    sqla.session.add(new_group)
                    sqla.session.commit()
                    gs.append(new_group)
                    flash(str(__('Add group success!')), 'success')
                    return redirect(url_for(request.endpoint))
                else:
                    flash(str(__('The form is not validated!')), 'error')

        # form delete submit
        if request.method == 'POST' and dform.data['submit_del']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif dform.validate_on_submit():
                del_group = sqla.session.query(models.Group) \
                    .filter_by(id=dform.id.data).one()
                del_group._deleted_at = func.now()
                if dform.modify_info.data:
                    del_group._modify_info = dform.modify_info.data
                sqla.session.commit()
                flash(str(__('Delete group success!')), 'success')
                return redirect(url_for(request.endpoint))

        return render_template('group/index.html', gs=gs,
                               form=form, dform=dform)
