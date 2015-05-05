from zope.interface import Interface
from zope.interface import implements
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component.hooks import getSite

from AccessControl import Unauthorized
from AccessControl import getSecurityManager
from zExceptions import NotFound

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from ploneintranet.activitystream.interfaces import IActivity

from .interfaces import IPloneIntranetActivitystreamLayer
from .interfaces import IStreamProvider
from .interfaces import IActivityProvider

from ploneintranet.activitystream.interfaces import IStatusActivity
from ploneintranet.activitystream.interfaces import IStatusActivityReply

from ploneintranet.core.integration import PLONEINTRANET

import logging

logger = logging.getLogger(__name__)


def date_key(item):
    if hasattr(item, 'effective'):
        # catalog brain
        return max(item.effective, item.created)
    # Activity
    return item.date


class StreamProvider(object):
    """Render activitystreams

    This is the core rendering logic that powers
    @@stream and @@activitystream_portal, and also
    ploneintranet.networking @@author
    """
    implements(IStreamProvider)
    adapts(Interface, IPloneIntranetActivitystreamLayer, Interface)

    index = ViewPageTemplateFile("templates/stream_provider.pt")

    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.view = self.__parent__ = view
        # @@stream renders this optionally with a tag filter
        self.tag = None
        # @@stream and ploneintranet.network:@@author
        # render this optionally with a users filter
        self.users = None
        self.microblog_context = PLONEINTRANET.context(context)

    def update(self):
        pass

    def render(self):
        return self.index()

    __call__ = render

    def activities(self):
        items = self._activities_statuses()
        # see date_key sorting function above
        items = sorted(items, key=date_key, reverse=True)

        i = 0
        for item in items:
            if i >= self.count:
                break
            try:
                activity = IActivity(item)
            except Unauthorized:
                continue
            except NotFound:
                logger.exception("NotFound: %s" % item.getURL())
                continue

            if self._activity_visible(activity):
                yield activity
                i += 1

    def _activity_visible(self, activity):
        if IStatusActivity.providedBy(activity):
            return True
        return False

    def _activities_statuses(self):
        container = PLONEINTRANET.microblog
        if not container:
            raise StopIteration()

        # filter on users OR context, not both
        if self.users:
            # support ploneintranet.network integration
            activities = container.user_values(self.users,
                                               limit=self.count,
                                               tag=self.tag)
        elif self.microblog_context:
            # support collective.local integration
            activities = container.context_values(self.microblog_context,
                                                  limit=self.count,
                                                  tag=self.tag)
        else:
            # default implementation
            activities = container.values(limit=self.count, tag=self.tag)

        # For a reply IStatusActivity we render the parent post and then
        # all the replies are inside that. So, here we filter out reply who's
        # parent post we already rendered.
        seen_thread_ids = []
        for activity in activities:
            if (activity.thread_id and activity.thread_id in seen_thread_ids) \
                    or activity.id in seen_thread_ids:
                continue

            if IStatusActivityReply.providedBy(activity):
                seen_thread_ids.append(activity.thread_id)
            else:
                seen_thread_ids.append(activity.id)

            yield activity

    def activity_providers(self):
        for activity in self.activities():
            if not self.can_view(activity):
                # discussion parent inaccessible
                continue

            yield getMultiAdapter(
                (activity, self.request, self.view),
                IActivityProvider)

    def can_view(self, activity):
        """Returns true if current user has the 'View' permission.
        """
        sm = getSecurityManager()
        if IStatusActivity.providedBy(activity):
            permission = "Plone Social: View Microblog Status Update"
            return sm.checkPermission(permission, self.context)

    def is_anonymous(self):
        portal_membership = getToolByName(getSite(),
                                          'portal_membership',
                                          None)
        return portal_membership.isAnonymousUser()

    @property
    def count(self):
        return 15
