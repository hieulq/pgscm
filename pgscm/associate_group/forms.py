from flask_wtf import FlaskForm
from wtforms import StringField, validators

from pgscm.utils import __


class AssociateGroupForm(FlaskForm):
    code = StringField(__('Associate group code'), validators=[
        validators.DataRequired(message=__('Associate group code '
                                           'required!'))])
