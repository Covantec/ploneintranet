# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from plone.app.layout.navigation.interfaces import INavigationRoot
from logging import getLogger
from plone.app.widgets.interfaces import IFieldPermissionChecker
from types import FunctionType
from zope.component import queryAdapter
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory
import inspect

from plone.app.content.browser.vocabulary import BaseVocabularyView
from plone.app.content.browser.vocabulary import VocabLookupException
from plone.app.content.browser.vocabulary import _parseJSON

logger = getLogger(__name__)

_permissions = {
    'ploneintranet.network.vocabularies.Keywords': 'Modify portal content',
}


class PersonalizedVocabularyView(BaseVocabularyView):
    """
    Queries a named personalized vocabulary and returns
    JSON-formatted results.

    Replaces plone.app.content.browser.vocabulary.VocabularyView
    """

    def get_context(self):
        return self.context

    def get_vocabulary(self):
        """
        Look up named vocabulary and check permissions.
        Unline p.a.content.browser.vocabulary.VocabularyView
        this resolves a IPersonalizedVocabularyFactory
        and calls it with both context and request to
        enable personalization.
        """
        # copy security checks
        # __init__ factory
        # skip legacy support
        # __call__ factory with (context, request)
        # return vocabulary

        logger.info(".get_vocabulary()")

        # --- unchanged upstream ---
        # Look up named vocabulary and check permission.
        context = self.context
        factory_name = self.request.get('name', None)
        field_name = self.request.get('field', None)
        if not factory_name:
            raise VocabLookupException('No factory provided.')
        authorized = None
        sm = getSecurityManager()
        if (factory_name not in _permissions or
                not INavigationRoot.providedBy(context)):
            # Check field specific permission
            if field_name:
                permission_checker = queryAdapter(context,
                                                  IFieldPermissionChecker)
                if permission_checker is not None:
                    authorized = permission_checker.validate(field_name,
                                                             factory_name)
            if not authorized:
                raise VocabLookupException('Vocabulary lookup not allowed')
        # Short circuit if we are on the site root and permission is
        # in global registry
        elif not sm.checkPermission(_permissions[factory_name], context):
            raise VocabLookupException('Vocabulary lookup not allowed')

        factory = queryUtility(IVocabularyFactory, factory_name)
        if not factory:
            raise VocabLookupException(
                'No factory with name "%s" exists.' % factory_name)

        # This part is for backwards-compatibility with the first
        # generation of vocabularies created for plone.app.widgets,
        # which take the (unparsed) query as a parameter of the vocab
        # factory rather than as a separate search method.
        if type(factory) is FunctionType:
            factory_spec = inspect.getargspec(factory)
        else:
            factory_spec = inspect.getargspec(factory.__call__)
        query = _parseJSON(self.request.get('query', ''))
        if query and 'query' in factory_spec.args:
            vocabulary = factory(context, query=query)
        else:
            # This is what is reached for non-legacy vocabularies.
            vocabulary = factory(context)

        return vocabulary
