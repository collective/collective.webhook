# -*- coding: utf-8 -*-
from collective.webhook.actions.datamanager import DataManager
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


def validate_payload(value):
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
        title=_("JSON Payload"),
        description=_("The payload you want to dispatch in JSON"),
        required=False,
        constraint=validate_payload,
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

    element = "plone.actions.Webhook"
    _v_requests = requests

    @property
    def summary(self):
        return _(
            "${method} ${url}",
            mapping=dict(method=self.method, url=self.url),
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


def submit(method: str, url: str, payload: dict, timeout: int, r: requests):
    """Call webhook"""
    try:
        if method == "POST":
            EXECUTOR.submit(r.post, url, json=payload, timeout=timeout)
        elif method == "FORM":
            for key in payload:
                payload[key] = json.dumps(payload[key]).strip('"')
            EXECUTOR.submit(r.post, url, data=payload, timeout=timeout)
        elif method == "GET":
            for key in payload:
                payload[key] = json.dumps(payload[key]).strip('"')
            EXECUTOR.submit(r.get, url, params=payload, timeout=timeout)
    except TypeError:
        logger.exception("Error calling webhook:")


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
        interpolator = IStringInterpolator(obj)
        payload = interpolate(json.loads(self.element.payload), interpolator)
        transaction.get().join(
            DataManager(
                functools.partial(submit, method, url, payload, self.timeout, r)
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
