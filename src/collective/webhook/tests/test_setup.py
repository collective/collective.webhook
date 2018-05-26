# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.webhook.testing import COLLECTIVE_WEBHOOK_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.webhook is properly installed."""

    layer = COLLECTIVE_WEBHOOK_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.webhook is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'collective.webhook'))

    def test_browserlayer(self):
        """Test that ICollectiveWebhookLayer is registered."""
        from collective.webhook.interfaces import (
            ICollectiveWebhookLayer)
        from plone.browserlayer import utils
        self.assertIn(
            ICollectiveWebhookLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_WEBHOOK_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['collective.webhook'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.webhook is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'collective.webhook'))

    def test_browserlayer_removed(self):
        """Test that ICollectiveWebhookLayer is removed."""
        from collective.webhook.interfaces import \
            ICollectiveWebhookLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            ICollectiveWebhookLayer,
            utils.registered_layers())
