# -*- coding: utf-8 -*-
"""Base module for unittesting."""
import base64
import unittest

from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

from plone.testing import z2

from ploneintranet.testing import PLONEINTRANET_FIXTURE

from ploneintranet.async.celerytasks import app


class PloneintranetAsyncLayer(PloneSandboxLayer):

    defaultBases = (PLONEINTRANET_FIXTURE,)

    def setUp(self):
        """Activate the async stack"""
        super(PloneintranetAsyncLayer, self).setUp()
        # force async regardless of buildout config
        app.conf.CELERY_ALWAYS_EAGER = False

    def tearDown(self):
        """Restore original environment"""
        super(PloneintranetAsyncLayer, self).tearDown()

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        import ploneintranet.async
        self.loadZCML(package=ploneintranet.async)

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        # Install into Plone site using portal_setup
        applyProfile(portal, 'ploneintranet.async:default')

    def tearDownZope(self, app):
        """Tear down Zope."""
        pass


FIXTURE = PloneintranetAsyncLayer()
INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,), name="PloneintranetAsyncLayer:Integration")
FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE, z2.ZSERVER_FIXTURE),  # NB ZServer enabled!
    name="PloneintranetAsyncLayer:Functional")


class BaseTestCase(unittest.TestCase):
    """Shared utils for integration and functional tests"""

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.portal.REQUEST

    def basic_auth(self, username='admin', password='secret'):
        # fake needed credentials at Post.__init__
        cred = base64.encodestring('%s:%s' % (username, password))
        self.request._auth = 'Basic %s' % cred.strip()


class IntegrationTestCase(BaseTestCase):
    """Base class for integration tests."""

    layer = INTEGRATION_TESTING


class FunctionalTestCase(BaseTestCase):
    """Base class for functional tests."""

    layer = FUNCTIONAL_TESTING
