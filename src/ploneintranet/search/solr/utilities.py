import collections
import logging
import urlparse

from Acquisition import aq_base
from plone import api
from zope.component import getUtility
from zope.interface import implementer

from .. import base
from ..interfaces import IQueryFilterFields
from ..interfaces import ISiteSearch
from .adapters import SearchResult
from .interfaces import IConnectionConfig
from .interfaces import IConnection
from .interfaces import IMaintenance
from .interfaces import IQuery
from .interfaces import IQueryFields


logger = logging.getLogger(__name__)


def prepare_data(data):
    """Prepare data (from Plone) for use with SOLR.

    Mutates the supplied mapping in-place.

    :param data: The data mapping.
    :type data: collections.MutableMapping
    """
    arau = data.get('allowedRolesAndUsers')
    if arau is not None:
        arau = list(v.replace(':', '$') for v in arau)
        data['allowedRolesAndUsers'] = arau


@implementer(IConnectionConfig)
class ConnectionConfig(object):

    _url = None

    def __init__(self, host, port, basepath, core):
        self.host = host
        self.port = port
        self.basepath = basepath.lstrip('/')
        self.core = core

    @classmethod
    def from_url(cls, url):
        pr = urlparse.urlparse(url)
        (host, port) = pr.netloc.split(':', 1)
        (basepath, core) = filter(bool, pr.path.split('/'))
        cfg = cls(host, port, '/' + basepath, core)
        return cfg

    @property
    def url(self):
        if self._url is None:
            format_url = 'http://{host}:{port}/{basepath}/{core}'.format
            self._url = format_url(**vars(self))
        return self._url


@implementer(IMaintenance)
class Maintenance(object):

    # AKA 'scorched.connection.SolrInterface'
    _conn = None

    @classmethod
    def _find_objects_to_index(cls, origin):
        """ generator to recursively find and yield all zope objects below
            the given start point """
        traverse = origin.unrestrictedTraverse
        basepath = '/'.join(origin.getPhysicalPath())
        cut = len(base) + 1
        paths = [basepath]
        for (idx, path) in enumerate(paths):
            obj = traverse(path)
            yield (path[cut:], obj)
            if hasattr(aq_base(obj), 'objectIds'):
                for id_ in obj.objectIds():
                    paths.insert(idx + 1, path + '/' + id_)

    def _get_connection(self):
        if self._conn is not None:
            return self._conn
        if self._conn is None:
            self._conn = IConnection(getUtility(IConnectionConfig))
        return self._get_connection()

    def warmup_spellchcker(self):
        """Build the Solr spellchecker."""
        search = IQuery(self._get_connection())
        response = search.query().spellcheck(build=True).execute()
        return response

    def purge(self):
        conn = self._get_connection()
        response = conn.delete_all()
        conn.commit(waitSearcher=True, expungeDeletes=True)
        conn.optimize(waitSearcher=True)
        return response


@implementer(ISiteSearch)
class SiteSearch(base.SiteSearch):
    """A Site search utility using SOLR as the engine.

    This implementation uses the `scorched` bindings to
    generate the lucene query used to deliver site search results.

    This logic combining the query and filter parameters to the query.

    The resulting logical query is similar to the following:

        ((Title == VALUE OR Description == VALUE OR SearchableText == VALUE)
        AND (FILTER1 == VALUE OR FILTER)
        AND (allowedRolesAndUsers=... OR allowedRolesAndUsers=..) ...

    """

    def __collect_query_params(self, iface, bucket):
        """Collect original query paramters for debugging purposes.

        :param iface: The Zope interface used for the query.
        :type iface: zope.interface.Interface
        :param bucket: The container which field names will be inserted.
        :type bucket: collections.MutableMapping
        """
        params = collections.OrderedDict()
        query_spec = iface['query']
        for name in query_spec.required:
            params[name] = bucket[name]
        for name in query_spec.optional:
            if name in bucket:
                params[name] = bucket[name]
        return params

    def _create_query_object(self, phrase):
        """Create the query object given the search `phrase`.

        :param phrase: The phrase to query SOLR with.
        :type phrase: sr
        :returns: A query object.
        :rtype query: ploneintranet.search.solr.search.Search
        """
        interface = IConnection(getUtility(IConnectionConfig))
        phrase_query = interface.Q()
        query_params = dict.fromkeys(tuple(IQueryFields), phrase)
        for query_param in query_params.items():
            phrase_query |= interface.Q(**dict([query_param]))
        return IQuery(interface).query(phrase_query)

    def _apply_filters(self, query, filters):
        interface = query.interface
        self._validate_query_fields(filters, IQueryFilterFields)
        return query.filter(interface.Q(**filters))

    def _apply_security(self, query):
        Q = query.interface.Q
        user = api.user.get_current()
        catalog = api.portal.get_tool(name='portal_catalog')
        arau = catalog._listAllowedRolesAndUsers(user)
        data = dict(allowedRolesAndUsers=arau)
        prepare_data(data)
        arau_q = Q()
        for entry in data.pop('allowedRolesAndUsers'):
            arau_q |= Q(allowedRolesAndUsers=entry)
        return query.filter(arau_q)

    def _apply_facets(self, query):
        return query.facet_by(fields=self._facet_fields)

    def _apply_date_range(self, query, start_date, end_date):
        filter_query = query.filter
        if start_date and end_date:
            query = filter_query(created__range=(start_date, end_date))
        elif end_date is not None:
            query = filter_query(created__lt=end_date)
        else:
            query = filter_query(created__gt=start_date)
        return query

    def _apply_spellchecking(self, query, phrase):
        return query.spellcheck(q=phrase, collate=True, maxCollations=1)

    def _paginate(self, query, start, step):
        return query.paginate(start=start, rows=step)

    def _apply_ordering(self, query):
        return query.sort_by('-created')

    def _apply_debugging(self, query):
        return query.debug()

    def _execute(self, query, debug=False, **kw):
        response = query.execute(constructor=SearchResult.from_indexed_result)
        query_params = self.__collect_query_params(ISiteSearch, dict(kw))
        response.query_params = query_params
        return response
