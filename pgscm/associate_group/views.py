from flask import render_template, current_app, request, \
    flash, redirect, url_for
from flask_security import roles_accepted, current_user
from sqlalchemy import func

import uuid

from . import agroup
from .forms import AssociateGroupForm

from pgscm import sqla
from pgscm.db import models
from pgscm.utils import __, DeleteForm, check_role
from pgscm import const as c

crud_role = c.ADMIN_MOD_ROLE


@agroup.route('/vi/lien-nhom', endpoint='index_vi', methods=['GET', 'POST'])
@agroup.route('/en/associate-group', endpoint='index_en',
              methods=['GET', 'POST'])
@roles_accepted(*c.ALL_ROLES)
def index():
    form = AssociateGroupForm()
    dform = DeleteForm()

    if current_app.config['AJAX_CALL_ENABLED']:
        form.province_id.choices = []
        return render_template('agroup/index.html', form=form, dform=dform)
    else:
        province_id = current_user.province_id
        if province_id:
            ags = models.AssociateGroup.query.filter_by(
                province_id=province_id, _deleted_at=None).order_by(
                                models.AssociateGroup.name.asc()).all()
            form.province_id.choices = [
                (p.province_id, p.type + " " + p.name) for p in
                models.Province.query.filter_by(province_id=province_id).all()]
        else:
            ags = models.AssociateGroup.query.filter_by(_deleted_at=None)\
                .order_by(models.AssociateGroup.name.asc()).all()
            form.province_id.choices = []
            # form.province_id.choices = [
            #     (p.province_id, p.type + " " + p.name) for p in
            #     models.Province.query.order_by(
            #         models.Province.name.asc()).all()]

        # form create or edit submit
        if request.method == 'POST' and form.data['submit']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))

            form.province_id.choices = [(form.province_id.data, form.province_id.label.text)]
            # edit associate group
            if form.id.data:
                if form.validate_on_submit():
                    edit_agroup = sqla.session.query(models.AssociateGroup) \
                        .filter_by(id=form.id.data).one()
                    edit_agroup.email = form.email.data
                    edit_agroup.associate_group_code = form \
                        .associate_group_code.data
                    edit_agroup.name = form.name.data
                    if edit_agroup.province_id != form.province_id.data:
                        edit_agroup.province = models.Province.query \
                            .filter_by(province_id=form.province_id.data) \
                            .one()
                    flash(str(__('Update associate group success!')),
                          'success')
                    return redirect(url_for(request.endpoint))
                else:
                    flash(str(__('The form is not validated!')), 'error')

            # add associate group
            else:
                form.id.data = str(uuid.uuid4())
                if form.validate_on_submit():
                    province = sqla.session.query(models.Province) \
                        .filter_by(province_id=form.province_id.data).one()
                    as_group = form.associate_group_code.data
                    new_agroup = models.AssociateGroup(
                        id=form.id.data,
                        associate_group_code=as_group,
                        name=form.name.data, province=province,
                        email=form.email.data,
                    )
                    sqla.session.add(new_agroup)
                    sqla.session.commit()
                    flash(str(__('Add associate group success!')), 'success')
                    return redirect(url_for(request.endpoint))

                else:
                    flash(str(__('The form is not validated!')), 'error')

                    # form delete submit
        if request.method == 'POST' and dform.data['submit_del']:
            if not check_role(crud_role):
                return redirect(url_for(request.endpoint))
            elif dform.validate_on_submit():
                del_agroup = sqla.session.query(models.AssociateGroup) \
                    .filter_by(id=dform.id.data).one()
                del_agroup._deleted_at = func.now()
                if dform.modify_info.data:
                    del_agroup._modify_info = dform.modify_info.data
                sqla.session.commit()
                flash(str(__('Delete associate group success!')), 'success')
                return redirect(url_for(request.endpoint))

        return render_template('agroup/index.html', ags=ags,
                               form=form, dform=dform)
