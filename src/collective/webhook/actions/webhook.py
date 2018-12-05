# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules import PloneMessageFactory as _
from plone.contentrules.rule.interfaces import IExecutable
from plone.contentrules.rule.interfaces import IRuleElementData
from plone.stringinterp.interfaces import IStringInterpolator
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.interfaces import IValidator
from z3c.form.util import getSpecification
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import ValidationError
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import json
import logging
import os
import requests


try:
    from plone.app.contentrules.browser.formhelper import ContentRuleFormWrapper  # noqa: E501
    from plone.app.contentrules.actions import ActionAddForm
    from plone.app.contentrules.actions import ActionEditForm
    PLONE_4 = False
except ImportError:
    from plone.app.contentrules.browser.formhelper import AddForm as ActionAddForm  # noqa: E501
    from plone.app.contentrules.browser.formhelper import EditForm as ActionEditForm  # noqa: E501
    from zope.formlib import form
    PLONE_4 = True


logger = logging.getLogger('collective.webhook')

methods = SimpleVocabulary([
    SimpleTerm(value=u'GET', title=_(u'GET')),
    SimpleTerm(value=u'POST', title=_(u'POST')),
    SimpleTerm(value=u'FORM', title=_(u'POST FORM')),
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
    """Definition of the configuration available for a webhook action
    """
    url = schema.URI(
        title=_(u'Webhook URL'),
        required=True,
    )
    method = schema.Choice(
        title=_(u'Call method'),
        vocabulary=methods,
    )
    payload = schema.Text(
        title=_(u'JSON Payload'),
        description=_(u'The payload you want to dispatch in JSON'),
        required=False,
        constraint=validate_payload,
    )


@implementer(IValidator)
@adapter(
    None,
    None,
    None,
    getSpecification(IWebhookAction['payload']),
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

    url = u''
    method = u''
    payload = u''

    element = 'plone.actions.Webhook'
    requests = requests

    @property
    def summary(self):
        return _(
            u'${method} ${url}',
            mapping=dict(method=self.method, url=self.url),
        )


def interpolate(value, interpolator):
    """Recursively interpolate supported values"""
    if isinstance(value, unicode):
        return interpolator(value).strip()
    elif isinstance(value, list):
        return [interpolate(v, interpolator) for v in value]
    elif isinstance(value, dict):
        return dict([(k, interpolate(v, interpolator))
                     for k, v in value.items()])
    return value


EXECUTOR = ThreadPoolExecutor(max_workers=1)


@implementer(IExecutable)
@adapter(Interface, IWebhookAction, Interface)
class WebhookActionExecutor(object):
    """The executor for this action.
    """
    timeout = 120

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        method = self.element.method
        r = self.element.requests
        url = self.element.url
        obj = self.event.object
        interpolator = IStringInterpolator(obj)
        payload = interpolate(json.loads(self.element.payload), interpolator)
        try:
            if method == 'POST':
                EXECUTOR.submit(
                    r.post, url, json=payload, timeout=self.timeout
                )
            elif method == 'FORM':
                for key in payload:
                    payload[key] = json.dumps(payload[key]).strip('"')
                EXECUTOR.submit(
                    r.post, url, data=payload, timeout=self.timeout
                )
            elif method == 'GET':
                for key in payload:
                    payload[key] = json.dumps(payload[key]).strip('"')
                EXECUTOR.submit(
                    r.get, url, params=payload, timeout=self.timeout
                )
        except TypeError:
            logger.exception('Error calling webhook:')
        return True


class WebhookAddForm(ActionAddForm):
    """
    An add form for the webhook action
    """
    schema = IWebhookAction
    label = _(u'Add Webhook Action')
    description = _(
        u'A webhook action can execute HTTP GET or POST with '
        u'interpolated  JSON payload.'
    )
    form_name = _(u'Configure element')
    Type = WebhookAction

    if PLONE_4:
        form_fields = form.FormFields(IWebhookAction)
        template = ViewPageTemplateFile(
            os.path.join('templates', 'webhook_p4.pt'),
        )

        def create(self, data):
            a = WebhookAction()
            form.applyChanges(a, self.form_fields, data)
            return a

    else:
        template = ViewPageTemplateFile(
            os.path.join('templates', 'webhook.pt'),
        )


if PLONE_4:
    class WebhookAddFormView(WebhookAddForm):
        pass
else:
    class WebhookAddFormView(ContentRuleFormWrapper):
        form = WebhookAddForm


class WebhookEditForm(ActionEditForm):
    """
    An edit form for the webhook action
    """
    schema = IWebhookAction
    label = _(u'Edit Webhook Action')
    description = _(
        u'A webhook action can execute HTTP GET or POST with '
        u'interpolated  JSON payload.'
    )
    form_name = _(u'Configure element')

    if PLONE_4:
        form_fields = form.FormFields(IWebhookAction)
        template = ViewPageTemplateFile(
            os.path.join('templates', 'webhook_p4.pt'),
        )
    else:
        template = ViewPageTemplateFile(
            os.path.join('templates', 'webhook.pt'),
        )


if PLONE_4:
    class WebhookEditFormView(WebhookEditForm):
        pass
else:
    class WebhookEditFormView(ContentRuleFormWrapper):
        form = WebhookEditForm
