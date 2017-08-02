from flask_babelex import gettext
from flask_babelex import ngettext
from flask_babelex import lazy_gettext

from flask import flash
from flask_wtf import FlaskForm
from flask_security import current_user
from flask_potion.contrib.alchemy import SQLAlchemyManager
from flask_potion.instances import Pagination

from wtforms.widgets.core import Select as BaseSelectWidget
from wtforms.widgets.core import Input as SubmitWidget
from wtforms import TextAreaField, SubmitField, HiddenField

from sqlalchemy import exc

from pgscm import const
from pgscm.db import models

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


class Submit(SubmitWidget):
    def __init__(self, input_type='submit'):
        super(Submit, self).__init__(input_type)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('value', field.label.text)
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = c + " " + const.SUBMIT_DEFAULT_CLASS
        return super(Submit, self).__call__(field, **kwargs)


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
        if r == current_user.roles[0].name:
            return True
    flash(str(__('You have no permission!')), 'warning')
    return False


def email_is_exist(email):
    try:
        models.User.query.filter_by(
            email=email).one()
        return True
    except exc.SQLAlchemyError:
        return False


class PgsPotionManager(SQLAlchemyManager):
    def paginated_instances_or(self, page, per_page, where=None, sort=None):
        instances = self.instances_or(where=where, sort=sort)
        if isinstance(instances, list):
            return Pagination.from_list(instances, page, per_page)
        return self._query_get_paginated_items(instances, page, per_page)

    def instances_or(self, where=None, sort=None):
        query = self._query()

        if query is None:
            return []

        if where:
            expressions = [self._expression_for_condition(condition)
                           for condition in where]
            query = self._query_filter(query, self._or_expression(expressions))

        return self._query_order_by(query, sort)
