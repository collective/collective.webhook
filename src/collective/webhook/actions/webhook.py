# -*- coding: utf-8 -*-
from collective.webhook.actions.datamanager import DataManager
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import (
    AddForm as ActionAddForm,  # noqa: E501
)
from plone.app.contentrules.browser.formhelper import (
    EditForm as ActionEditForm,  # noqa: E501
)
from plone.contentrules.rule.interfaces import IExecutable
from plone.contentrules.rule.interfaces import IRuleElementData
from plone.stringinterp.interfaces import IStringInterpolator
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from urllib.parse import urlencode
from z3c.form.interfaces import IValidator
from z3c.form.util import getSpecification
from zope import schema
from zope.component import adapter
from zope.formlib import form
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import ValidationError
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import functools
import json
import logging
import os
import requests
import transaction


logger = logging.getLogger("collective.webhook")

methods = SimpleVocabulary([
    SimpleTerm(value="GET", title=_("GET")),
    SimpleTerm(value="POST", title=_("POST")),
    SimpleTerm(value="FORM", title=_("POST FORM")),
])


def validate_json(value):
    try:
        if value is not None:
            json.loads(value)
    except (ValueError, TypeError) as e:

        class JSONValidationError(ValidationError):
            __doc__ = str(e)

        raise JSONValidationError()
    return True


class IWebhookAction(Interface):
    """Definition of the configuration available for a webhook action"""

    url = schema.URI(
        title=_("Webhook URL"),
        required=True,
    )
    method = schema.Choice(
        title=_("Call method"),
        vocabulary=methods,
    )
    payload = schema.Text(
        title=_("JSON payload"),
        description=_("The payload you want to dispatch in JSON"),
        required=False,
        constraint=validate_json,
    )
    headers = schema.Text(
        title=_("JSON headers"),
        description=_("The headers you want to dispatch in JSON"),
        required=False,
        constraint=validate_json,
    )
    verbose = schema.Bool(
        title=_("Verbose logging"),
        description=_("Whether to log the call and the response"),
    )


@implementer(IValidator)
@adapter(
    None,
    None,
    None,
    getSpecification(IWebhookAction["payload"]),
    None,
)
class PayloadValidator(object):
    def __init__(self, context, request, form, field, widget):
        self.field = field

    def validate(self, value):
        try:
            if value is not None:
                json.loads(value)
        except (ValueError, TypeError) as e:
            raise Invalid(e)


@implementer(IWebhookAction, IRuleElementData)
class WebhookAction(SimpleItem):
    """
    The implementation of the action defined before
    """

    url = ""
    method = ""
    payload = ""
    headers = ""
    verbose = False

    element = "plone.actions.Webhook"
    _v_requests = requests

    @property
    def summary(self):
        verbose = getattr(self, "verbose", False)
        return _(
            "${method} ${url}${verbose}",
            mapping=dict(
                method=self.method,
                url=self.url,
                verbose=" (verbose)" if verbose else "",
            ),
        )


def interpolate(value, interpolator):
    """Recursively interpolate supported values"""
    if isinstance(value, str):
        return interpolator(value).strip()
    elif isinstance(value, list):
        return [interpolate(v, interpolator) for v in value]
    elif isinstance(value, dict):
        return dict([(k, interpolate(v, interpolator)) for k, v in value.items()])
    return value


EXECUTOR = ThreadPoolExecutor(max_workers=1)


def build_curl_cmd(method, url, headers=None, payload=None, form=False) -> str:
    """Build a curl command example for logging."""
    curl_cmd = ["curl", "-X", method, url]
    if headers:
        for k, v in headers.items():
            curl_cmd.extend(["-H", f"{k}: {v}"])
    if method == "POST" and not form and payload is not None:
        curl_cmd.extend(["-H", f'"Content-Type: application/json"'])
        curl_cmd.extend(["-d", f"'{json.dumps(payload)}'"])
    elif form and payload:
        for k, v in payload.items():
            curl_cmd.extend(["-F", f'"{k}={v}"'])
    return " ".join(curl_cmd)


def submit(
    method: str,
    url: str,
    headers: dict,
    payload: dict,
    timeout: int,
    verbose: bool,
    r: requests,
):
    """Call webhook"""
    try:
        futures = []
        if method == "POST":
            if verbose:
                logger.info(build_curl_cmd("POST", url, headers, payload))
            futures.append(
                EXECUTOR.submit(r.post, url, headers, json=payload, timeout=timeout)
            )
        elif method == "FORM":
            for key in payload:
                payload[key] = json.dumps(payload[key]).strip('"')
            if verbose:
                logger.info(build_curl_cmd("POST", url, headers, payload, form=True))
            futures.append(
                EXECUTOR.submit(
                    r.post, url, data=payload, headers=headers, timeout=timeout
                )
            )
        elif method == "GET":
            for key in payload:
                payload[key] = json.dumps(payload[key]).strip('"')
            if verbose:
                url_with_params = url
                if payload:
                    url_with_params = f"{url}?{urlencode(payload)}"
                logger.info(build_curl_cmd("GET", url_with_params, headers))
            futures.append(EXECUTOR.submit(r.get, url, params=payload, timeout=timeout))
        for future in as_completed(futures):
            response = future.result()
            if verbose:
                logger.info(response.text)
            response.raise_for_status()
    except Exception as e:
        logger.exception("Error calling webhook: %s", e)


@implementer(IExecutable)
@adapter(Interface, IWebhookAction, Interface)
class WebhookActionExecutor(object):
    """The executor for this action."""

    timeout = 120

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        method = self.element.method
        r = self.element._v_requests
        url = self.element.url
        obj = self.event.object
        verbose = getattr(self.element, "verbose", False)
        interpolator = IStringInterpolator(obj)
        payload = interpolate(json.loads(self.element.payload), interpolator)
        headers = interpolate(
            json.loads(getattr(self.element, "headers", "{}") or "{}"), interpolator
        )
        transaction.get().join(
            DataManager(
                functools.partial(
                    submit, method, url, headers, payload, self.timeout, verbose, r
                )
            )
        )
        return True


class WebhookAddForm(ActionAddForm):
    """
    An add form for the webhook action
    """

    schema = IWebhookAction
    label = _("Add Webhook Action")
    description = _(
        "A webhook action can execute HTTP GET or POST with interpolated  JSON payload."
    )
    form_name = _("Configure element")
    Type = WebhookAction
    form_fields = form.FormFields(IWebhookAction)
    template = ViewPageTemplateFile(
        os.path.join("templates", "webhook.pt"),
    )

    def create(self, data):
        a = WebhookAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class WebhookAddFormView(WebhookAddForm):
    pass


class WebhookEditForm(ActionEditForm):
    """
    An edit form for the webhook action
    """

    schema = IWebhookAction
    label = _("Edit Webhook Action")
    description = _(
        "A webhook action can execute HTTP GET or POST with interpolated  JSON payload."
    )
    form_name = _("Configure element")

    form_fields = form.FormFields(IWebhookAction)
    template = ViewPageTemplateFile(
        os.path.join("templates", "webhook.pt"),
    )


class WebhookEditFormView(WebhookEditForm):
    pass
