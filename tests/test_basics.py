import unittest
import mock
from flask import current_app
from pgscm import create_app, api


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(api, 'add_resource'):
            self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app = None
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
