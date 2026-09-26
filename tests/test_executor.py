# -*- coding: utf-8 -*-
from collective.webhook.actions.webhook import IWebhookAction
from collective.webhook.actions.webhook import PayloadValidator
from collective.webhook.actions.webhook import validate_json
from collective.webhook.actions.webhook import WebhookAction
from collective.webhook.actions.webhook import WebhookActionExecutor
from collective.webhook.actions.webhook import WebhookAddForm
from collective.webhook.testing import COLLECTIVE_WEBHOOK_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from tests import drain_executor
from plone.app.testing import TEST_USER_ID
from plone.stringinterp.interfaces import IStringInterpolator
from plone.uuid.interfaces import IUUID
from types import SimpleNamespace
from zope.interface import Invalid
from zope.schema import ValidationError

import transaction
import unittest


class Recorder(object):
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append(("post", args, kwargs))

    get = post


class ExecutorTests(unittest.TestCase):
    layer = COLLECTIVE_WEBHOOK_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Folder", "section", title="Section")
        self.folder = self.portal["section"]

    def execute(self, **properties):
        element = WebhookAction()
        element.url = "http://localhost:8080/"
        element.method = "POST"
        element.payload = '{"url": "${url}", "n": 1, "tags": ["${title}"]}'
        for key, value in properties.items():
            setattr(element, key, value)
        element._v_requests = Recorder()
        event = SimpleNamespace(object=self.folder)
        self.assertTrue(WebhookActionExecutor(self.portal, element, event)())
        return element._v_requests

    def wait_for(self, recorder):
        drain_executor()
        return recorder.calls

    def test_post_with_interpolated_headers(self):
        recorder = self.execute(
            headers='{"X-Url": "${url}", "X-Tags": ["a"]}', verbose=True
        )
        # nothing is sent before the transaction commits
        self.assertEqual([], recorder.calls)
        with self.assertLogs("collective.webhook", "INFO"):
            transaction.commit()
            calls = self.wait_for(recorder)
        ((name, args, kwargs),) = calls
        self.assertEqual("post", name)
        self.assertEqual(("http://localhost:8080/",), args)
        self.assertEqual(
            {"url": "http://nohost/plone/section", "n": 1, "tags": ["Section"]},
            kwargs["json"],
        )
        self.assertEqual(
            {"X-Url": "http://nohost/plone/section", "X-Tags": ["a"]},
            kwargs["headers"],
        )

    def test_missing_or_empty_headers_are_empty(self):
        for headers in ("", None):
            recorder = self.execute(headers=headers)
            transaction.commit()
            ((name, args, kwargs),) = self.wait_for(recorder)
            self.assertEqual({}, kwargs["headers"])

    def test_element_without_headers_attribute(self):
        element = WebhookAction()
        element.url = "http://localhost:8080/"
        element.method = "GET"
        element.payload = "{}"
        element._v_requests = Recorder()
        del WebhookAction.headers
        try:
            WebhookActionExecutor(
                self.portal, element, SimpleNamespace(object=self.folder)
            )()
            transaction.commit()
            ((name, args, kwargs),) = self.wait_for(element._v_requests)
        finally:
            WebhookAction.headers = ""
        self.assertEqual({}, kwargs["headers"])

    def test_aborted_transaction_sends_nothing(self):
        recorder = self.execute()
        transaction.abort()
        drain_executor()
        self.assertEqual([], recorder.calls)

    def test_summary(self):
        element = WebhookAction()
        element.method = "GET"
        element.url = "http://x/"
        self.assertEqual("GET http://x/", self.render(element.summary))
        element.verbose = True
        self.assertEqual("GET http://x/ (verbose)", self.render(element.summary))

    def render(self, message):
        from zope.i18n import interpolate

        return interpolate(str(message), message.mapping)

    def test_add_form_create(self):
        form = WebhookAddForm(self.portal, self.layer["request"])
        action = form.create({
            "url": "http://x/",
            "method": "POST",
            "payload": "{}",
            "headers": '{"a": "b"}',
            "verbose": True,
        })
        self.assertIsInstance(action, WebhookAction)
        self.assertEqual("http://x/", action.url)
        self.assertEqual("POST", action.method)
        self.assertEqual('{"a": "b"}', action.headers)
        self.assertTrue(action.verbose)

    def test_uuid_substitutions(self):
        interpolator = IStringInterpolator(self.folder)
        self.assertEqual(IUUID(self.folder), interpolator("${uid}"))
        self.assertEqual(IUUID(self.portal), interpolator("${parent_uid}"))


class ValidationTests(unittest.TestCase):
    def test_validate_json_accepts_json_and_none(self):
        self.assertTrue(validate_json('{"a": 1}'))
        self.assertTrue(validate_json(None))

    def test_validate_json_rejects_invalid_json(self):
        with self.assertRaises(ValidationError):
            validate_json("{not json")
        with self.assertRaises(ValidationError):
            validate_json(1)

    def test_payload_validator(self):
        validator = PayloadValidator(None, None, None, IWebhookAction["payload"], None)
        self.assertIsNone(validator.validate('{"a": 1}'))
        self.assertIsNone(validator.validate(None))
        with self.assertRaises(Invalid):
            validator.validate("{not json")
