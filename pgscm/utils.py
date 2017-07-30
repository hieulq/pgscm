from flask_babelex import gettext
from flask_babelex import ngettext
from flask_babelex import lazy_gettext

from flask import flash
from flask_wtf import FlaskForm
from flask_security import current_user

from wtforms.widgets.core import Select as BaseSelectWidget
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


class DeleteForm(FlaskForm):
    id = HiddenField(__('Id'))
    modify_info = TextAreaField(
        __('Reason'),
        render_kw={
            "placeholder": __('Describe your reasons to delete this data')})
    submit_del = SubmitField(__('Delete'))


def check_role(roles):
    for r in roles:
        if r == current_user.roles[0].name:
            return True
    flash(str(__('You have no permission!')), 'warning')
    return False
