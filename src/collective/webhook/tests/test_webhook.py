# -*- coding: utf-8 -*-
from collective.webhook.actions.webhook import WebhookAction
from collective.webhook.testing import COLLECTIVE_WEBHOOK_FUNCTIONAL_TESTING
from collective.webhook.utils import create_tarball
from plone.app.testing import login
from plone.app.testing import PLONE_SITE_ID
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleAction
from zope.annotation import IAnnotations
from zope.component import getUtility

import os
import time
import unittest


class WebhookTests(unittest.TestCase):
    layer = COLLECTIVE_WEBHOOK_FUNCTIONAL_TESTING

    def setUp(self):
        tarball = create_tarball(
            os.path.join(os.path.dirname(__file__), 'profile_01')
        )
        self.layer['portal'].portal_setup.runAllImportStepsFromProfile(
            None, purge_old=False, archive=tarball
        )

    def test_action_registered(self):
        element = getUtility(IRuleAction, name='plone.actions.Webhook')
        self.assertEqual(element.addview, 'plone.actions.Webhook')
        self.assertEqual(element.editview, 'edit')

    def test_rule_imported(self):
        portal = self.layer['portal']

        rule = portal.restrictedTraverse('++rule++rule-1')
        self.assertEqual(rule.title, u'HTTP GET')
        self.assertEqual(len(rule.actions), 1)

        action = rule.actions[0]
        self.assertIsInstance(action, WebhookAction)
        self.assertEqual(action.method, 'GET')
        self.assertEqual(action.url, 'http://localhost:8080/')
        self.assertEqual(action.payload, '{"url": "${url}"}')

        ann = IAnnotations(rule)
        self.assertIn(
            '/' + PLONE_SITE_ID, ann['plone.app.contentrules.ruleassignments']
        )

    def test_execute_rules(self):
        portal = self.layer['portal']

        class Mock(object):
            def __init__(self, log):
                self.log = log

            def get(self, *args, **kwargs):
                self.log.append((args, kwargs))

            def post(self, *args, **kwargs):
                self.log.append((args, kwargs))

        storage = getUtility(IRuleStorage)
        storage.active = True

        get = []
        rule = portal.restrictedTraverse('++rule++rule-1')
        action = rule.actions[0]
        action.requests = Mock(get)

        post = []
        rule = portal.restrictedTraverse('++rule++rule-2')
        action = rule.actions[0]
        action.requests = Mock(post)

        form = []
        rule = portal.restrictedTraverse('++rule++rule-3')
        action = rule.actions[0]
        action.requests = Mock(form)

        login(portal, TEST_USER_NAME)
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Folder', 'section')  # noqa: P001

        for i in range(10):
            if len(get) and len(post) and len(form):
                break
            # let thread pool worker to work
            time.sleep(0.1)

        self.assertEqual('http://localhost:8080/', get[0][0][0])
        self.assertEqual({
            'url': 'http://nohost/plone/section'
        }, get[0][1]['params'])

        self.assertEqual('http://localhost:8080/', post[0][0][0])
        self.assertEqual({
            'url': 'http://nohost/plone/section'
        }, post[0][1]['json'])

        self.assertEqual('http://localhost:8080/', form[0][0][0])
        self.assertEqual({
            'url': 'http://nohost/plone/section'
        }, form[0][1]['data'])
