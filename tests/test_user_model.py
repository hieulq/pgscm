import unittest
import mock
from app import create_app, sqla, api
from app.db.models import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(api, 'add_resource'):
            self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        sqla.create_all()

    def tearDown(self):
        sqla.session.remove()
        sqla.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password is not None)
