# coding=utf-8
from plone import api
from ploneintranet.core import ploneintranetCoreMessageFactory as _
from ploneintranet.workspace.browser.cart_actions.base import BaseCartView
from ploneintranet.workspace.interfaces import IGroupingStoragable
from ploneintranet.workspace.interfaces import IGroupingStorage
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from urllib import urlencode

import logging


log = logging.getLogger(__name__)


class RetagView(BaseCartView):

    def confirm(self):
        index = ViewPageTemplateFile("templates/retag_confirmation.pt")
        return index(self)

    def retag(self):
        handled = []
        uids = self.request.form.get('uids', [])
        new_tags = self.request.form.get('subjects')
        if not new_tags:
            return
        storage = (IGroupingStoragable.providedBy(self.workspace) and
                   IGroupingStorage(self.workspace) or None)
        for uid in uids:
            obj = api.content.get(UID=uid)
            if obj:
                tags_set = set(obj.subject)
                for tag in new_tags.split(','):
                    tags_set.add(safe_unicode(tag))
                obj.subject = tuple(tags_set)
                obj.reindexObject()
                if storage:
                    storage.update_groupings(obj)
                handled.append(u'"%s"' % safe_unicode(obj.Title()))
        if handled:
            titles = ', '.join(sorted(handled))
            msg = _(
                u"batch_retag_success",
                default=u"The following items have been (re)tagged: ${title_elems}",  # noqa
                mapping={"title_elems": titles}
            )
            api.portal.show_message(
                message=msg,
                request=self.request,
                type="success",
            )
        else:
            api.portal.show_message(
                message=_(u"No items could be (re)tagged"),
                request=self.request,
                type="info",
            )

        params = {
            'groupname': self.request.get('groupname', ''),
        }
        self.request.response.redirect(
            '{0}?{1}'.format(
                self.context.absolute_url(), urlencode(params)))
