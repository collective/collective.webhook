# -*- coding: utf-8 -*-
from collective.webhook.actions.webhook import build_curl_cmd
from collective.webhook.actions.webhook import interpolate
from collective.webhook.actions.webhook import submit

import unittest


class Response(object):
    text = "response body"

    def __init__(self, error=None):
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error


class Recorder(object):
    """Stand-in for the requests module that records calls"""

    def __init__(self, error=None, response_error=None):
        self.calls = []
        self.error = error
        self.response_error = response_error

    def _call(self, name, args, kwargs):
        self.calls.append((name, args, kwargs))
        if self.error:
            raise self.error
        return Response(self.response_error)

    def get(self, *args, **kwargs):
        return self._call("get", args, kwargs)

    def post(self, *args, **kwargs):
        return self._call("post", args, kwargs)


URL = "http://localhost:8080/"
HEADERS = {"Authorization": "Bearer token"}


class InterpolateTests(unittest.TestCase):
    def upper(self, value):
        return value.upper() + "  "

    def test_string_is_interpolated_and_stripped(self):
        self.assertEqual("ABC", interpolate("abc", self.upper))

    def test_list_is_interpolated_recursively(self):
        self.assertEqual(["A", ["B"]], interpolate(["a", ["b"]], self.upper))

    def test_dict_is_interpolated_recursively(self):
        self.assertEqual(
            {"k": {"n": ["V"]}}, interpolate({"k": {"n": ["v"]}}, self.upper)
        )

    def test_other_values_are_kept(self):
        self.assertEqual(
            [1, 1.5, True, None], interpolate([1, 1.5, True, None], self.upper)
        )


class BuildCurlCmdTests(unittest.TestCase):
    def test_get_with_headers(self):
        self.assertEqual(
            "curl -X GET http://x/ -H Authorization: Bearer token",
            build_curl_cmd("GET", "http://x/", HEADERS),
        )

    def test_post_json(self):
        cmd = build_curl_cmd("POST", "http://x/", None, {"a": 1})
        self.assertIn("-X POST", cmd)
        self.assertIn('-H "Content-Type: application/json"', cmd)
        self.assertIn("-d '{\"a\": 1}'", cmd)

    def test_post_form(self):
        cmd = build_curl_cmd("POST", "http://x/", None, {"a": "1"}, form=True)
        self.assertIn('-F "a=1"', cmd)
        self.assertNotIn("Content-Type", cmd)


class SubmitTests(unittest.TestCase):
    def test_post_sends_headers_and_json(self):
        r = Recorder()
        submit("POST", URL, dict(HEADERS), {"a": 1}, 5, False, r)
        ((name, args, kwargs),) = r.calls
        self.assertEqual("post", name)
        # headers must not slip into the positional ``data`` argument
        self.assertEqual((URL,), args)
        self.assertEqual(HEADERS, kwargs["headers"])
        self.assertEqual({"a": 1}, kwargs["json"])
        self.assertEqual(5, kwargs["timeout"])

    def test_form_sends_headers_and_data(self):
        r = Recorder()
        submit("FORM", URL, dict(HEADERS), {"a": "x", "b": 2}, 5, False, r)
        ((name, args, kwargs),) = r.calls
        self.assertEqual("post", name)
        self.assertEqual((URL,), args)
        self.assertEqual(HEADERS, kwargs["headers"])
        self.assertEqual({"a": "x", "b": "2"}, kwargs["data"])

    def test_get_sends_headers_and_params(self):
        r = Recorder()
        submit("GET", URL, dict(HEADERS), {"a": "x", "b": 2}, 5, False, r)
        ((name, args, kwargs),) = r.calls
        self.assertEqual("get", name)
        self.assertEqual((URL,), args)
        self.assertEqual(HEADERS, kwargs["headers"])
        self.assertEqual({"a": "x", "b": "2"}, kwargs["params"])

    def test_not_verbose_does_not_log(self):
        with self.assertNoLogs("collective.webhook", "INFO"):
            submit("POST", URL, {}, {"a": 1}, 5, False, Recorder())

    def test_verbose_post_logs_call_and_response(self):
        with self.assertLogs("collective.webhook", "INFO") as logs:
            submit("POST", URL, dict(HEADERS), {"a": 1}, 5, True, Recorder())
        self.assertEqual(2, len(logs.records))
        self.assertIn("curl -X POST", logs.records[0].getMessage())
        self.assertIn("Authorization: Bearer token", logs.records[0].getMessage())
        self.assertEqual("response body", logs.records[1].getMessage())

    def test_verbose_form_logs_call_and_response(self):
        with self.assertLogs("collective.webhook", "INFO") as logs:
            submit("FORM", URL, {}, {"a": "1"}, 5, True, Recorder())
        self.assertIn('-F "a=1"', logs.records[0].getMessage())
        self.assertEqual("response body", logs.records[1].getMessage())

    def test_verbose_get_logs_url_with_query(self):
        with self.assertLogs("collective.webhook", "INFO") as logs:
            submit("GET", URL, {}, {"a": "1"}, 5, True, Recorder())
        self.assertIn(
            "curl -X GET http://localhost:8080/?a=1", logs.records[0].getMessage()
        )

    def test_verbose_get_without_payload_logs_plain_url(self):
        with self.assertLogs("collective.webhook", "INFO") as logs:
            submit("GET", URL, {}, {}, 5, True, Recorder())
        self.assertEqual(
            "curl -X GET http://localhost:8080/", logs.records[0].getMessage()
        )

    def test_none_payload_is_accepted_for_all_methods(self):
        for method in ("POST", "FORM", "GET"):
            r = Recorder()
            submit(method, URL, {}, None, 5, True, r)
            ((name, args, kwargs),) = r.calls
            self.assertFalse(
                kwargs.get("json") or kwargs.get("data") or kwargs.get("params")
            )

    def test_request_error_is_logged_not_raised(self):
        r = Recorder(error=RuntimeError("boom"))
        with self.assertLogs("collective.webhook", "ERROR") as logs:
            submit("POST", URL, {}, {}, 5, False, r)
        self.assertIn("Error calling webhook: boom", logs.records[0].getMessage())

    def test_http_error_status_is_logged_not_raised(self):
        r = Recorder(response_error=RuntimeError("500 Server Error"))
        with self.assertLogs("collective.webhook", "ERROR") as logs:
            submit("GET", URL, {}, {}, 5, False, r)
        self.assertIn("500 Server Error", logs.records[0].getMessage())

    def test_unknown_method_calls_nothing(self):
        r = Recorder()
        submit("PUT", URL, {}, {}, 5, False, r)
        self.assertEqual([], r.calls)
