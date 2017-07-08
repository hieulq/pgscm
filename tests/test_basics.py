import unittest
import mock
from flask import current_app
from app import create_app, sqla, api


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(api, 'add_resource'):
            self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        sqla.create_all()

    def tearDown(self):
        self.app = None
        sqla.session.remove()
        sqla.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
