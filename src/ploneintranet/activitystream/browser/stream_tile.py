# coding=utf-8
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
from plone.memoize.view import memoize
from plone.tiles import Tile
from ploneintranet import api as piapi
from ploneintranet.userprofile.content.userprofile import IUserProfile
import logging

logger = logging.getLogger(__name__)


class StreamTile(Tile):
    '''Tile view similar to StreamView.'''

    index = ViewPageTemplateFile("templates/stream_tile.pt")
    count = 15

    def __init__(self, context, request):
        self.context = context
        self.request = request
        # BBB: the or None should be moved to the microblog methods
        self.tag = self.data.get('tag') or None
        if 'last_seen' in request:
            self.last_seen = request.get('last_seen')
        else:
            self.last_seen = None
        self.stop_asking = False

    @property
    def next_max(self):
        if self.last_seen:
            return long(self.last_seen) - 1
        else:
            return None

    @property
    @memoize
    def toLocalizedTime(self):
        ''' Facade for the toLocalizedTime method
        '''
        return api.portal.get_tool('translation_service').toLocalizedTime

    @property
    @memoize
    def microblog_context(self):
        ''' Returns the microblog context
        '''
        return piapi.microblog.get_microblog_context(self.context)

    def filter_statusupdates(self, statusupdates):
        ''' This method filters the microblog StatusUpdates

        The idea is:
         - if a StatusUpdate is a comment return the parent StatusUpdate
         - show threads only once
        The effectiveness of this is limited by the autoexpand:
        the current view "sees" only it's current 15 updates.

        Additionally, this performs a postprocessing filter on content updates
        in case a user has access to a microblog_context workspace
        but not to the (unpublished) content_context object
        '''
        seen_thread_ids = set()
        good_statusupdates = []
        container = piapi.microblog.get_microblog()

        for su in statusupdates:
            if su.thread_id and su.thread_id in seen_thread_ids:
                # a reply on a toplevel we've already seen
                continue
            elif su.id in seen_thread_ids:
                # a toplevel we've already seen
                continue

            if su.thread_id:
                # resolve reply into toplevel
                su = container.get(su.thread_id)

            # process a thread only once
            seen_thread_ids.add(su.id)

            # content updates postprocessing filter
            try:
                su.content_context
            except AttributeError:  # = unauthorized
                # skip thread on inaccessible content (e.g. draft)
                continue

            good_statusupdates.append(su)

        return good_statusupdates

    def get_statusupdates(self):
        ''' This will return all the StatusUpdates which are not comments

        The activity are sorted by reverse chronological order
        '''
        container = piapi.microblog.get_microblog()
        stream_filter = self.request.get('stream_filter')
        if self.microblog_context:
            # support ploneintranet.workspace integration
            statusupdates = container.context_values(
                self.microblog_context,
                max=self.next_max,
                limit=self.count,
                tag=self.tag
            )
        elif IUserProfile.providedBy(self.context):
            # Get the updates for this user
            statusupdates = container.user_values(
                self.context.username,
                max=self.next_max,
                limit=self.count,
                tag=self.tag
            )
        elif stream_filter == 'network':
            # Only activities from people I follow
            graph = api.portal.get_tool("ploneintranet_network")
            userid = api.user.get_current().id
            following = graph.unpack(
                graph.get_following(u'user', userid))
            following.append(userid)  # show own updates, as well
            statusupdates = container.user_values(
                following,
                max=self.next_max,
                limit=self.count,
                tag=self.tag
            )
        elif stream_filter in ('interactions', 'posted', 'likes'):
            raise NotImplementedError("unsupported stream filter: %s"
                                      % stream_filter)
        else:
            # default implementation: all activities
            statusupdates = container.values(
                max=self.next_max,
                limit=self.count,
                tag=self.tag
            )
        return statusupdates

    @property
    @memoize
    def statusupdates_autoexpand(self):
        ''' The list of our activities
        '''
        # unfiltered for autoexpand management
        statusupdates = [x for x in self.get_statusupdates()]

        # filtered for display
        for su in self.filter_statusupdates(statusupdates):
            yield su

        # stop autoexpand when last batch is empty
        if len(statusupdates) == 0:
            self.stop_asking = True
        else:
            self.last_seen = statusupdates[-1].id

    @property
    @memoize
    def post_views(self):
        ''' The activity as views
        '''
        for statusupdate in self.statusupdates_autoexpand:
            yield api.content.get_view(
                'post.html',
                statusupdate,
                self.request
            )
