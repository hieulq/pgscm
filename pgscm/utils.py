from flask_babelex import gettext
from flask_babelex import ngettext
from flask_babelex import lazy_gettext

from flask_wtf import FlaskForm

from wtforms.widgets.core import Select as BaseSelectWidget
from wtforms import TextAreaField

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
    modify_info = TextAreaField(
        __('Reason'),
        render_kw={
            "placeholder": __('Describe your reasons to delete this data')})
