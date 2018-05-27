# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.actions import ActionAddForm
from plone.app.contentrules.actions import ActionEditForm
from plone.app.contentrules.browser.formhelper import ContentRuleFormWrapper
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
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import json
import logging
import os
import requests


logger = logging.getLogger('collective.webhook')

methods = SimpleVocabulary([
    SimpleTerm(value=u'GET', title=_(u'GET')),
    SimpleTerm(value=u'POST', title=_(u'POST')),
])


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
        description=_(u'The payload you want to POST'),
        required=False,
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
        json.loads(value)


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
                payload = json.dumps(payload)
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
    template = ViewPageTemplateFile(os.path.join('templates', 'webhook.pt'))


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
    template = ViewPageTemplateFile(os.path.join('templates', 'webhook.pt'))


class WebhookEditFormView(ContentRuleFormWrapper):
    form = WebhookEditForm
