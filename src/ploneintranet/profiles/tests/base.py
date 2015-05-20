import unittest2 as unittest
from plone.testing import z2
from plone.app.testing.interfaces import SITE_OWNER_NAME
from plone.app.testing import login
from plone.app.testing import logout
from ploneintranet.profiles.testing import \
    PLONEINTRANET_PROFILES_INTEGRATION_TESTING


class BaseTestCase(unittest.TestCase):

    layer = PLONEINTRANET_PROFILES_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.portal.REQUEST

    def login(self, username):
        """
        helper method to login as specific user

        :param username: the username of the user to add to the group
        :type username: str
        :rtype: None

        """
        login(self.portal, username)

    def logout(self):
        """
        helper method to avoid importing the p.a.testing logout method
        """
        logout()

    def login_as_portal_owner(self):
        """
        helper method to login as site admin
        """
        z2.login(self.app['acl_users'], SITE_OWNER_NAME)
