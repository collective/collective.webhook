# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import collective.webhook


class CollectiveWebhookLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=collective.webhook)


COLLECTIVE_WEBHOOK_FIXTURE = CollectiveWebhookLayer()

COLLECTIVE_WEBHOOK_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_WEBHOOK_FIXTURE, ),
    name='CollectiveWebhookLayer:IntegrationTesting',
)

COLLECTIVE_WEBHOOK_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_WEBHOOK_FIXTURE, ),
    name='CollectiveWebhookLayer:FunctionalTesting',
)

COLLECTIVE_WEBHOOK_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_WEBHOOK_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='CollectiveWebhookLayer:AcceptanceTesting',
)
