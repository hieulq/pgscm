from flask_babelex import gettext
from flask_babelex import ngettext
from flask_babelex import lazy_gettext

from flask import flash, jsonify
from flask_wtf import FlaskForm
from flask_security import current_user
from flask_potion.contrib.alchemy import SQLAlchemyManager
from flask_potion.instances import Pagination, Instances as BaseInst

from sqlalchemy import func

from wtforms.widgets.core import Select as BaseSelectWidget
from wtforms.widgets.core import Input
from wtforms import TextAreaField, SubmitField, HiddenField

from pgscm import const as c

from pgscm import const

_ = gettext
_n = ngettext
__ = lazy_gettext


class Select(BaseSelectWidget):
    def __init__(self, multiple=False):
        super(Select, self).__init__(multiple)

    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = c + " " + const.SELECT_DEFAULT_ID
        return super(Select, self).__call__(field, **kwargs)


class MultiSelect(BaseSelectWidget):
    def __init__(self, multiple=True):
        super(MultiSelect, self).__init__(multiple)

    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = c + " " + const.MULTI_SELECT_DEFAULT_CLASS
        return super(MultiSelect, self).__call__(field, **kwargs)


class Submit(Input):
    def __init__(self, input_type='submit'):
        super(Submit, self).__init__(input_type)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('value', field.label.text)
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = c + " " + const.SUBMIT_DEFAULT_CLASS
        return super(Submit, self).__call__(field, **kwargs)


class Date(Input):
    def __init__(self, input_type='date'):
        super(Date, self).__init__(input_type)


class DeleteForm(FlaskForm):
    id = HiddenField(__('Id'))
    modify_info = TextAreaField(
        __('Reason'),
        render_kw={
            "placeholder": __('Describe your reasons to delete this data')})
    submit_del = SubmitField(__('Delete!'), id=const.DEL_SUBMIT_ID,
                             widget=Submit())


def check_role(roles):
    for r in roles:
        for user_role in current_user.roles:
            if r == user_role.name:
                return True
    flash(str(__('You have no permission!')), 'warning')
    return False


def is_region_role():
    nation_role = c.NATION_ROLE
    for user_role in current_user.roles:
        if user_role in nation_role:
            return False
    return True


def convert_filters(value, field_filters):
    if isinstance(value, dict) and len(value) == 1:
        filter_name = next(iter(value))

        # search for filters in the format {"$filter": condition}
        if len(filter_name) > 1 and filter_name.startswith('$'):
            filter_name = filter_name[1:]

            for filter in field_filters.values():
                if filter_name == filter.name:
                    return filter.convert(value)

    filter = field_filters[None]
    return filter.convert(value)


def delete_farmer(farmer_id, sqla, models, modify_info):
    farmer_delete = sqla.session.query(models.Farmer) \
            .filter_by(id=farmer_id).one()
    farmer_delete._deleted_at = func.now()
    if modify_info:
        farmer_delete._modify_info = modify_info

    cert_of_farmer_deleted = sqla.session.query(models.Certificate)\
        .filter_by(owner_farmer_id=farmer_id).all()
    for cert in cert_of_farmer_deleted:
        cert._deleted_at = func.now()

    sqla.session.commit()


def delete_group(group_id, sqla, models, modify_info):
    group_delete = sqla.session.query(models.Group) \
        .filter_by(id=group_id).one()
    group_delete._deleted_at = func.now()
    if modify_info:
        group_delete._modify_info = modify_info

    cert_of_group_deleted = sqla.session.query(models.Certificate) \
        .filter_by(owner_group_id=group_id).all()
    for cert in cert_of_group_deleted:
        cert._deleted_at = func.now()

    farmer_of_group_deleted = sqla.session.query(models.Farmer) \
        .filter_by(group_id=group_id).all()
    for f in farmer_of_group_deleted:
        delete_farmer(f.id, sqla, models, "")

    sqla.session.commit()


def delete_agroup(agroup_id, sqla, models, modify_info):
    agroup_delete = sqla.session.query(models.AssociateGroup) \
        .filter_by(id=agroup_id).one()
    agroup_delete._deleted_at = func.now()
    if modify_info:
        agroup_delete._modify_info = modify_info

    group_of_agroup_deleted = sqla.session.query(models.Group) \
        .filter_by(associate_group_id=agroup_id).all()
    for g in group_of_agroup_deleted:
        delete_group(g.id, sqla, models, "")

    sqla.session.commit()


def soft_delete(sqla, object_del, models):
    dform = DeleteForm()
    if dform.validate_on_submit():
        if object_del == "farmer":
            delete_farmer(dform.id.data, sqla, models, dform.modify_info.data)
            success_message = str(__('Delete farmer success!'))
        elif object_del == "group":
            delete_group(dform.id.data, sqla, models, dform.modify_info.data)
            success_message = str(__('Delete group success!'))
        elif object_del == "agroup":
            delete_agroup(dform.id.data, sqla, models, dform.modify_info.data)
            success_message = str(__('Delete associate group success!'))
        elif object_del == "certificate":
            cert_delete = sqla.session.query(models.Certificate) \
                .filter_by(id=dform.id.data).one()
            cert_delete._deleted_at = func.now()
            if dform.modify_info.data:
                cert_delete._modify_info = dform.modify_info.data
            sqla.session.commit()
            success_message = str(__('Delete certificate success!'))
        else:
            return jsonify(is_success=False,
                           message=str(__('Not valid soft delete form!')))
        return jsonify(is_success=True,
                       message=success_message)
    else:
        return jsonify(is_success=False,
                       message=str(__('The form is not validate!')))


class Instances(BaseInst):

    def _field_filters_schema(self, filters):
        if len(filters) == 1:
            return next(iter(filters.values())).request
        else:
            filt = [{
                "type": "array",
                "items": {
                    "anyOf": [filter.request for filter in
                              filters.values()]
                },
                "additionalItems": True}]
            return {"anyOf": filt + [filter.request for filter in
                                     filters.values()]}

    def _convert_filters(self, where):
        for name, value in where.items():
            if isinstance(value, list):
                for val in value:
                    yield convert_filters(val, self._filters[name])
            else:
                yield convert_filters(value, self._filters[name])


class PgsPotionManager(SQLAlchemyManager):
    def paginated_instances_or(self, page, per_page, where=None, sort=None,
                               filter_or_cols=[], filter_and_cols=[]):
        instances = self.instances_or(where=where, sort=sort,
                                      filter_or_cols=filter_or_cols,
                                      filter_and_cols=filter_and_cols)
        if isinstance(instances, list):
            return Pagination.from_list(instances, page, per_page)
        return self._query_get_paginated_items(instances, page, per_page)

    def instances_or(self, where=None, sort=None, filter_or_cols=[],
                     filter_and_cols=[]):
        filter_and_cols += ['id', '_deleted_at', 'group_id']
        query = self._query()

        if query is None:
            return []

        if where:
            and_where = ()
            or_where = ()
            or_filter = ()
            for cond in where:
                if cond.attribute in filter_and_cols:
                    and_where += (cond, )
                elif cond.attribute in filter_or_cols:
                    or_filter += (cond, )
                else:
                    or_where += (cond, )
            or_filter_expressions = [self._expression_for_condition(condition)
                                     for condition in or_filter]
            or_expressions = [self._expression_for_condition(condition)
                              for condition in or_where]
            and_expressions = [self._expression_for_condition(condition)
                               for condition in and_where]
            or_exp = self._or_expression(or_expressions)
            and_expressions.append(or_exp)
            if or_filter_expressions:
                filter_exp = self._or_expression(or_filter_expressions)
                and_expressions.append(filter_exp)
            query = self._query_filter(query, self._and_expression(
                and_expressions))

        return self._query_order_by(query, sort)
