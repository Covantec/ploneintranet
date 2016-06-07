# -*- coding=utf-8 -*-
from BTrees import OOBTree
from DateTime import DateTime
from plone import api
from ploneintranet import api as pi_api
from ploneintranet.microblog.interfaces import IMicroblogTool
from ploneintranet.microblog.statusupdate import StatusUpdate
from transaction import commit
from zope.component import queryUtility
import logging

logger = logging.getLogger('ploneintranet.microblog.migration')
PROFILE_ID = 'ploneintranet.microblog:default'


def setup_uuid_mapping(context):
    """0.5 adds a new index"""
    tool = queryUtility(IMicroblogTool)
    if not hasattr(tool, '_uuid_mapping'):
        logger.info("Adding missing UUID mapping to %s" % repr(tool))
        tool._uuid_mapping = OOBTree.OOBTree()
        commit()


def setup_threadids(context):
    """0.6 adds a new statuscontainerindex and statusupdate attribute"""
    tool = queryUtility(IMicroblogTool)
    if not hasattr(tool, '_threadid_mapping'):
        logger.info("Adding missing threadid mapping to %s" % repr(tool))
        tool._threadid_mapping = OOBTree.OOBTree()
        commit()
    i = 0
    for status in tool.values(limit=None):
        i += 1
        if getattr(status, 'thread_id', False) is False:
            status.thread_id = None
        if i % 100 == 0:
            commit()
    commit()


def uuid_to_microblog_uuid(context):
    '''
    In #506 the status update attribute
    _context_uuid was renamed _microblog_context_uuid

    This upgrade steps makes the existing content uptodate
    '''
    tool = queryUtility(IMicroblogTool)
    i = 0
    for status in tool.values(limit=None):
        if (
            isinstance(status, StatusUpdate) and
            not hasattr(status, '_microblog_context_uuid')
        ):
            i += 1
            uuid = getattr(status, '_context_uuid', None)
            status._microblog_context_uuid = uuid
        if i % 100 == 0:
            commit()
    commit()


def enforce_parent_context(context):
    '''
    A reply to a post should always inherit the security context
    of the thread parent.
    '''
    tool = queryUtility(IMicroblogTool)
    i = 0
    for status in tool.values(limit=None):
        if status.thread_id:
            i += 1
            # unindex old context uuid value
            old_uuid = status._microblog_context_uuid
            try:
                tool._uuid_mapping[old_uuid].remove(status.id)
            except KeyError:
                # idempotent
                pass
            # re-initialize microblog_context on statusupdate
            status._init_microblog_context(status.thread_id, None)
            # reindex new context uuid value
            tool._idx_context(status)
        if i % 100 == 0:
            commit()
    logger.info("Fixed security context for %s replies", i)
    commit()


def document_discussion_fields(context):
    '''Add new fields introduced for document discussion'''
    tool = queryUtility(IMicroblogTool)
    tool._update_ctime()
    if not hasattr(tool, '_content_uuid_mapping'):
        logger.info("Adding missing content_uuid mapping to %s" % repr(tool))
        tool._content_uuid_mapping = OOBTree.OOBTree()
    for status in tool._status_mapping.values():
        if not hasattr(status, '_content_context_uuid'):
            status._content_context_uuid = None
        if not hasattr(status, '_verb'):
            status._verb = None
    logger.info("Added document discussion fields")
    commit()


def statusupdate_edit_delete(context):
    """Upgrade for edit/delete feature"""
    tool = queryUtility(IMicroblogTool)
    tool._update_ctime()
    setup = api.portal.get_tool('portal_setup')
    # setup new edit/delete permissions
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    commit()


def discuss_older_docs(context):
    """Add document discussion on pre-existing documents.
    This only adds a 'created' message, since we cannot reconstruct
    the publication date and actor.
    """
    logger.info("Adding streams to older content")
    mtool = queryUtility(IMicroblogTool)
    haveseen = [x for x in mtool._content_uuid_mapping.keys()]
    ctool = api.portal.get_tool('portal_catalog')
    i = 0
    for brain in ctool.unrestrictedSearchResults(
            {'portal_type': [
                'Document', 'File', 'Image', 'Event', 'News Item']}):
        if brain.UID in haveseen:
            continue
        created = brain.created
        if isinstance(created, DateTime):
            created = created.asdatetime()
        pi_api.microblog.statusupdate.create(
            content_context=brain.getObject(),
            action_verb=u'created',
            userid=brain.Creator,
            time=created,
        )
        haveseen.append(brain.UID)
        i += 1
    logger.info("Added streams to %s older content objects", i)
    commit()
