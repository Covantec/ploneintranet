# -*- coding: utf-8 -*-
from plone import api

from ploneintranet.userprofile.tests.base import BaseTestCase


class TestAuth(BaseTestCase):

    def setUp(self):
        super(TestAuth, self).setUp()
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.portal.REQUEST
        self.login_as_portal_owner()
        self.profiles = api.content.create(
            title="Profiles",
            type="ploneintranet.userprofile.userprofilecontainer",
            container=self.portal)
        self.mtool = api.portal.get_tool('membrane_tool')

    def test_profile_is_membrane_type(self):
        self.assertIn(
            'ploneintranet.userprofile.userprofile',
            self.mtool.listMembraneTypes())

    def test_user_login(self):
        params = {
            'username': 'johndoe',
            'first_name': u'John',
            'last_name': u'Doe',
            'email': "johndoe@example.com",
            'password': 'secret',
            'confirm_password': 'secret'}
        profile = api.content.create(
            container=self.profiles,
            type='ploneintranet.userprofile.userprofile',
            id='johndoe',
            **params)

        self.mtool.reindexObject(profile)

        self.logout()
        self.login('johndoe')
        user = api.user.get_current()
        self.assertEqual(
            profile.username,
            user.getUserName())

        self.logout()
        with self.assertRaises(ValueError):
            self.login('janedoe')
