from Acquisition import aq_parent
from collective.webhook import _
from plone.stringinterp.adapters import BaseSubstitution
from plone.stringinterp.interfaces import IStringSubstitution
from plone.uuid.interfaces import IUUID
from zope.component import adapter
from zope.interface import Interface


@adapter(Interface)
class UUIDSubstitution(BaseSubstitution):
    category = _("All Content")
    description = _("Unique identifier of the content")

    def safe_call(self):
        return IUUID(self.context)


@adapter(Interface)
class ParentUUIDSubstitution(BaseSubstitution):
    category = _("All Content")
    description = _("Unique identifier of the parent content")

    def safe_call(self):
        return IUUID(aq_parent(self.context))
