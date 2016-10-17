# coding=utf-8
from AccessControl.security import checkPermission

from datetime import datetime
from DateTime import DateTime

from plone import api
from plone.tiles import Tile

from ploneintranet.calendar.utils import get_calendars
from ploneintranet.layout.app import apps_container_id
from ploneintranet.workspace.utils import parent_workspace
from ploneintranet.workspace.interfaces import IBaseWorkspaceFolder

from Products.CMFCore.permissions import ModifyPortalContent
from ploneintranet.calendar.utils import get_timezone_info
from ploneintranet.calendar.config import TZ_COOKIE_NAME

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


class FullCalendarTile(Tile):
    '''FullCalendar as a tile, used in cal app and workspace calendar'''

    @property
    def app(self):
        portal = api.portal.get()
        return getattr(portal, apps_container_id).calendar

    @property
    def today(self):
        now = datetime.now()
        return now.strftime("%a, %d %b %Y")

    def get_start_date(self):
        current_date = datetime.now()
        current_day = current_date.day
        current_month = current_date.month
        current_year = current_date.year
        try:
            day = int(self.request.form.get("day") or current_day)
        except ValueError:
            day = current_day
        try:
            month = int(self.request.form.get("month") or current_month)
        except ValueError:
            month = current_month
        try:
            year = int(self.request.form.get("year") or current_year)
        except ValueError:
            year = current_year
        datestr = "{year}-{month:0=2}-{day:0=2}".format(year=year,
                                                        month=month,
                                                        day=day)
        return datestr

    def _format_date_time(self, date_time, is_whole_day):
        if isinstance(date_time, DateTime):
            date_time = date_time.asdatetime()
        # 2012-02-18T09:00Z
        date_time_short = date_time.strftime('%Y-%m-%d')
        # 18 February 2012, 9:00
        date_time_long = date_time.strftime('%d %B %Y')

        if not is_whole_day:
            short_time = date_time.strftime("%H:%MZ")
            long_time = date_time.strftime("%H:%M%Z")
            date_time_short += "T" + short_time  # XXX Handle timezone
            date_time_long += ", " + long_time
        return (date_time_short, date_time_long)

    def _get_event_date_times(self, event):
        is_whole_day = event.whole_day
        event_dtimes = {}
        if event.start:
            (event_dtimes["start_date_time_short"],
             event_dtimes["start_date_time_long"]) = self._format_date_time(
                 event.start, is_whole_day)
        if event.end:
            (event_dtimes["end_date_time_short"],
             event_dtimes["end_date_time_long"]) = self._format_date_time(
                 event.end, is_whole_day)

        return event_dtimes

    def _get_event_class(self, event, calendar):
        """take the classes and add alien if appropriate in context"""

        classes = set(('cal-event',))

        # This assumes that an event always is placed right within a workspace.
        # Reason: Obviously getting the event and its workspace is expensive
        # and ading an index for it seems too much as well, but can be done if
        # this assumption proves to be not valid anymore.
        path = event.url
        workspace_id = path.split('/')[-2]
        classes.add("cal-cat-{0}".format(workspace_id))
        classes.add("cal-cat-{0}-{1}".format(workspace_id, calendar))

        is_whole_day = event.whole_day
        if is_whole_day:
            classes.add('all-day')

        classes.add("cal-cat-{0}".format(event.ws_type))
        classes.add("cal-cat-{0}-{1}".format(event.ws_type, calendar))

        current_ws = parent_workspace(self.context)
        if current_ws is not None and \
           IBaseWorkspaceFolder.providedBy(current_ws):
            if current_ws.id != workspace_id:
                classes.add('cal-cat-alien')

        if checkPermission(ModifyPortalContent, self.context):
            classes.add('editable')

        return " ".join(classes)

    def get_events(self):
        """ get events for calendar, provide proper classes """
        events = []
        events_by_calendar = get_calendars(self.context)['events']
        for calendar in events_by_calendar:
            ev_by_cal = events_by_calendar[calendar]
            for event in ev_by_cal:
                classes = self._get_event_class(event, calendar)
                edict = {}
                # Create a dict representation of the search results
                # XXX: This is something to be done properly once we abstract
                # use of solr into the pi_api
                edict = event.context.copy()
                edict.update(event.__dict__.copy())
                del edict['context']
                del edict['response']
                edict['classes'] = classes
                edict['url'] = event.url
                edict.update(self._get_event_date_times(event))

                events.append(edict)
        return events

    def get_timezone_data(self):
        timezone_vocab = getUtility(IVocabularyFactory,
                                    'ploneintranet.calendar.timezones')
        timezone_data = []
        for item in timezone_vocab:
            zoneinfo = get_timezone_info(item.token)
            timezone_data.append(zoneinfo)
        return timezone_data

    def get_user_timezone(self):
        return self.get_timezone_cookie(self)

    def set_user_timezone(self, tz):
        self.set_timezone_cookie(self, tz)

    def get_timezone_cookie(self, context):
        return context.request.get(TZ_COOKIE_NAME, 'Europe/Berlin')

    def set_timezone_cookie(self, context, tz):
        if tz:
            cookie_path = '/' + api.portal.get().absolute_url(1)
            context.request.response.setCookie(TZ_COOKIE_NAME, tz,
                                               path=cookie_path)
