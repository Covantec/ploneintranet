# coding=utf-8
from json import loads
from logging import getLogger
from plone import api
from plone.memoize.view import memoize
from ploneintranet.core import ploneintranetCoreMessageFactory as _
from ploneintranet.layout.browser.base import BaseView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


logger = getLogger(__name__)


class View(BaseView):
    ''' View used to render the on screen help tooltips

    You can also render links to fire the tooltip in pt, e.g.:

    <tal:bubble replace="structure python:osh_view.link_to('bubble-id')" />

    If 'bubble-id' is not a known bubble, the link will not be displayed

    The bubbles property merges the bubbles
    defined at the view level in the _bubbles class attribute and
    defined in the registry record ploneintranet.layout.custom_bubbles
    '''
    _link_to_template = ViewPageTemplateFile(
        "templates/on-screen-help-link.pt"
    )
    _fallback_bubble = {
        'title': _('Help unavailable'),
        'description': _('<p>404</p>'),
    }
    _bubbles = {
        'dashboard-view': {
            'title': _('Dashboard view select'),
            'description': _(
                'Here you can select different dashboards. '
                'There is an activity centric and a task '
                'centric dashboard available. You can also '
                'configure your own dashboard using My view. '
                'Pick what best fits your style of working.'
            ),
            'next': '',
        },
        'hamburger': {
            'title': _('Menu toggle'),
            'description': _(
                'The menu toggle lets you hide and show the '
                'global navigation which allows you to quickly '
                'jump to another section of the intranet.'
            ),
            'next': '',
        },
        'portal-suite': {
            'title': _('Welcome!'),
            'description': _(
                'We would like to introduce you to the '
                'Quaive Social Intranet Platform. Please try out!'
            ),
            'next': 'portal-dashboard',
        },
        'portal-dashboard': {
            'title': _('Dashboard'),
            'description': _(
                'This is the Dashboard. '
                'Here is the home for your personal shortcuts '
                'to your most important places. You can '
                'add workspaces, contacts and apps to '
                'your own dashboard.'
            ),
            'next': 'portal-news',
        },
        'portal-news': {
            'title': _('News'),
            'description': _(
                'Here is the news magazine. It gives you an overview '
                "over your company's actual news."
            ),
            'next': 'portal-library',
        },
        'portal-library': {
            'title': _('Library'),
            'description': _(
                'In the library you can find any documents '
                'that are informational for all intranet users.'
            ),
            'next': 'portal-workspaces',
        },
        'portal-workspaces': {
            'title': _('Workspaces'),
            'description': _(
                'This is workspaces section. Workspaces are '
                'areas for creating, organizing and sharing '
                'content. Go here to get an overview over the '
                'workspaces you can access.'
            ),
            'next': 'portal-apps',
        },
        'portal-apps': {
            'title': _('Apps'),
            'description': _(
                'Apps are extra bits of functionality for your '
                'Quaive site. Visit this section to find out what '
                'apps are available.'
            ),
            'next': '',
        },
        'portlet-bookmarks': {
            'title': _('Bookmarks portlet'),
            'description': _(
                'Bookmarks are what matters most to you. '
                'While browsing through the intranet, '
                'you can mark interesting content with a '
                'bookmark. All that content will then '
                'appear here in your bookmark box.'
            ),
            'next': '',
        },
        'portlet-contacts': {
            'title': _('Contacts portlet'),
            'description': _(
                'Quick access to all your contacts. Start '
                'typing a name, a job title or a street. '
                'Matching contacts appear immediately.'
            ),
            'next': '',
        },
        'portlet-events': {
            'title': _('Events portlet'),
            'description': _(
                'All events you are invited to - at your '
                'fingertips. They are ordered by upcoming '
                'first.',
            ),
            'next': '',
        },
        'portlet-library': {
            'title': _('Library portlet'),
            'description': _(
                'See recent changes to the library. '
                'Content listed here may be relevant for '
                'your next holiday application, show '
                'newest updates to the company manual or '
                "show you the latest article in the CEO's "
                'blog.'

            ),
            'next': '',
        },
        'portlet-news': {
            'title': _('News portlet'),
            'description': _(
                'Stay informed - see the latest news articles listed here. '
                "If you click the 'mark read' button of a news item "
                'it disappears from the portlet.'
            ),
            'next': '',
        },
        'portlet-tasks': {
            'title': _('Tasks portlet'),
            'description': _(
                'Your Tasks. This is what you need to work '
                'on, ordered by deadline. The topmost one is '
                'usually the one due first. If you just '
                "completed one, check it. If you don't yet "
                'know what to do, click it and read the '
                'description.'
            ),
            'next': '',
        },
        'portlet-workspaces': {
            'title': _('Workspaces portlet'),
            'description': _(
                'Your Workspaces! That are workspaces '
                'that you can see. You will never see '
                "any workspaces here that you can't "
                'actually access.'
            ),
            'next': '',
        },
        'portlet-bookmarked-workspaces': {
            'title': _('Bookmarked workspaces portlet'),
            'description': _(
                'Your bookmarked Workspaces! That are workspaces '
                'you marked as important by bookmarking them. '
                "You will never see any workspaces here that you can't "
                'actually access.'
            ),
            'next': '',
        },
        'portlet-bookmarked-apps': {
            'title': _('Bookmarked apps portlet'),
            'description': _(
                'Your bookmarked Apps! That are apps '
                'you marked as important by bookmarking them.'
            ),
            'next': '',
        },
        'portlet-stream': {
            'title': _('Activity stream portlet'),
            'description': _(
                "Read about what's going on in your company "
                'in the activity stream portlet. You can filter '
                'existing messages and also write a post '
                'to your colleagues yourself.'
            ),
            'next': '',
        },
        'post-message': {
            'title': _('Post a message'),
            'description': _(
                'Post a message to the team, to your '
                'colleagues, to the company. Share what is '
                'important right now, let your colleagues '
                'know. Upload attachments, mention specific '
                'people and tag your post.'
            ),
            'next': '',
        },
        'global-search': {
            'title': _('Portal search'),
            'description': _(
                'Use the search to find information within the Quaive portal.'
            ),
            'next': 'global-help-info',
        },
        'global-help-info': {
            'title': _('Help'),
            'description': _(
                'Use this toggle to turn the help bubbles on or off.'
            ),
            'next': 'global-chat-info',
        },
        'global-chat-info': {
            'title': _('Post a message'),
            'description': _(
                'Wanna chat with your collegues? Click here to open the '
                'chat app. A number within a red circle shows that you '
                'have unread chat messages.'
            ),
            'next': 'global-messages-info',
        },
        'global-messages-info': {
            'title': _('Post a message'),
            'description': _(
                'Notifications about news posts are listed here. '
                'A number within a red circle shows that you '
                'have unread notifications.'
            ),
            'next': 'global-personal-menu',
        },
        'global-personal-menu': {
            'title': _('Personal menu'),
            'description': _(
                'Your avatar image opens the personal menu with links to '
                'your user profile, password change and logout actions.'
            ),
            'next': '',
        }
    }

    @property
    @memoize
    def bubbles(self):
        ''' The bubbles are defined in a class attribute _bubbles
        and can be optionally be overridden through a registry record.
        For the moment the record accepts a json string, but this may change
        '''
        bubbles = self._bubbles.copy()
        custom_bubbles_json = api.portal.get_registry_record(
            'ploneintranet.layout.custom_bubbles',
            default='{}'
        )
        try:
            bubbles.update(loads(custom_bubbles_json))
        except:
            logger.error(
                'Invalid custom bubbles: check the registry record '
                'ploneintranet.layout.custom_bubbles'
            )
        return bubbles

    def link_to(self, bubbleid):
        ''' Create a bubble id link
        '''
        if bubbleid not in self.bubbles:
            return ''
        return self._link_to_template(bubbleid=bubbleid)

    @property
    @memoize
    def bubbleid(self):
        ''' Return the requested bubble id
        '''
        return self.request.form.get('q', '')

    def get_bubble(self):
        ''' The requested bubble
        '''
        bubble = {
            'id': 'osh-' + self.bubbleid,
        }
        bubble.update(
            self.bubbles.get(
                self.bubbleid,
                self._fallback_bubble
            )
        )
        return bubble
