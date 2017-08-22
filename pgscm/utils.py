from flask_babelex import gettext
from flask_babelex import ngettext
from flask_babelex import lazy_gettext

from flask import flash
from flask_wtf import FlaskForm
from flask_security import current_user
from flask_potion.contrib.alchemy import SQLAlchemyManager
from flask_potion.instances import Pagination, Instances as BaseInst

from wtforms.widgets.core import Select as BaseSelectWidget
from wtforms.widgets.core import Input
from wtforms import TextAreaField, SubmitField, HiddenField


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
                               filter_or_cols=[]):
        instances = self.instances_or(where=where, sort=sort,
                                      filter_or_cols=filter_or_cols)
        if isinstance(instances, list):
            return Pagination.from_list(instances, page, per_page)
        return self._query_get_paginated_items(instances, page, per_page)

    def instances_or(self, where=None, sort=None, filter_or_cols=[]):
        query = self._query()

        if query is None:
            return []

        if where:
            and_where = ()
            or_where = ()
            or_filter = ()
            for cond in where:
                if cond.attribute == 'province_id' \
                        or cond.attribute == '_deleted_at':
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
