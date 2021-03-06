# -*- coding: utf-8 -*-
from collections import defaultdict
from plone import api
from plone.app.textfield.interfaces import IRichTextValue
from plone.app.textfield.value import RichTextValue
from plone.autoform.interfaces import WIDGETS_KEY
from plone.autoform.widgets import ParameterizedWidget
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata
from plone.z3cform.z2 import processInputs
from ploneintranet.workspace.html_cleaners import sanitize_html
from Products.CMFPlone.utils import safe_unicode
from z3c.form.error import MultipleErrors
from z3c.form.interfaces import IDataConverter
from z3c.form.interfaces import IDataManager
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import NO_VALUE
from z3c.form.interfaces import NOT_CHANGED
from zope import component
from zope.schema import getFieldNames
from zope.schema import interfaces
from zope.schema import TextLine
import json
import logging

log = logging.getLogger(__name__)


def get_dexterity_schemas(context=None, portal_type=None):
    """ Utility method to get all schemas for a dexterity object.

        IMPORTANT: Either context or portal_type must be passed in, NOT BOTH.
        The idea is that for edit forms context is passed in and for add forms
        where we don't have a valid context we pass in portal_type.

        This builds on getAdditionalSchemata, which works the same way.
    """
    if context is not None:
        portal_type = context.portal_type

    fti = component.getUtility(IDexterityFTI, name=portal_type)
    schemas = [fti.lookupSchema()]
    for behavior_schema in \
            getAdditionalSchemata(context=context,
                                  portal_type=portal_type):
        if behavior_schema is not None:
            schemas.append(behavior_schema)
    return schemas


def dexterity_update(obj, request=None):
    """
    Utility method to update the fields of all the schemas of the Dexterity
    object 'obj'.
    """
    modified = defaultdict(list)
    if not request:
        request = obj.REQUEST
    # Call processInputs to decode strings to unicode, otherwise the
    # z3c.form dataconverters complain.
    processInputs(request)
    errors = []
    for schema in get_dexterity_schemas(context=obj):
        for name in getFieldNames(schema):
            # Only update fields which are included in the form
            # Look specifically for the empty-marker used to mark
            # empty checkboxes
            if name not in request.form and \
               '%s-empty-marker' % name not in request.form:
                continue
            field = schema[name]
            autoform_widgets = schema.queryTaggedValue(WIDGETS_KEY, default={})
            if name in autoform_widgets:
                widget = autoform_widgets[name]
                if not isinstance(widget, ParameterizedWidget):
                    widget = ParameterizedWidget(widget)
                widget = widget(field, request)
            else:
                widget = component.getMultiAdapter(
                    (field, request), IFieldWidget)

            widget.context = obj
            value = field.missing_value
            widget.update()
            try:
                raw = widget.extract()
            except MultipleErrors, e:
                errors.append(e)
                log.warn("Multiple errors while extracting field: %s" % name)
                continue

            if raw is NOT_CHANGED:
                continue

            if raw is NO_VALUE:
                continue

            if (
                IRichTextValue.providedBy(raw) and
                api.portal.get_registry_record(
                    'ploneintranet.workspace.sanitize_html')
            ):
                sanitized = RichTextValue(
                    raw=sanitize_html(safe_unicode(raw.raw)),
                    mimeType=raw.mimeType, outputMimeType=raw.outputMimeType)
                if sanitized.raw != raw.raw:
                    log.info(
                        'The HTML content of field "{}" on {} was sanitised.'.format(  # noqa
                            name, obj.absolute_url()))
                    raw = sanitized

            if isinstance(field, TextLine):
                # textLines must not contain line breaks (field contraint)
                # to prevent a ConstraintNotSatisfied error in `toFieldValue`
                raw = u" ".join(safe_unicode(raw).splitlines())

            try:
                value = IDataConverter(widget).toFieldValue(safe_unicode(raw))
            except Exception, exc:
                log.warn("Error in converting value for %s: %s (%s)"
                         % (name, raw, str(exc)))
                raise exc

            try:
                field.validate(value)
            except interfaces.RequiredMissing, e:
                errors.append(e)
                log.warn("Required field have missing value: %s" % name)
                # XXX: we might not want to continue here, since we then remove
                # the ability to remove field values. Client side validation
                # should prevent this situation from arising, but it's not yet
                # perfect.
                # continue
            except interfaces.ConstraintNotSatisfied, e:
                log.warn("Constraint not satisfied for field: %s" % name)
                log.warn(e)
                continue
            except interfaces.WrongType, e:
                log.warn("Wrong type for field: %s" % name)
                log.warn(e)
                continue

            # Get the datamanager and get the original value
            dm = component.getMultiAdapter((obj, field), IDataManager)

            # Only update the data, if it is different
            # or we can not get the original value, in which case we can not
            # check. Or it is an Object, in case we'll never know
            if (not dm.canAccess() or
                    dm.query() != value or
                    interfaces.IObject.providedBy(field)):
                dm.set(value)
                modified[schema].append(name)
    return dict(modified), errors


def get_selection_classes(context, field, default=None):
    """ identify all groups in the invitees """
    acl_users = api.portal.get_tool('acl_users')
    field_value = getattr(context, field, default)
    if not field_value:
        return ''
    assigned_users = field_value.split(',')
    selection_classes = {}
    for assignee_id in assigned_users:
        group = acl_users.getGroupById(assignee_id)
        if group:
            group_title = (
                group.getProperty('title') or group.getId() or assignee_id)
            selection_classes[group_title] = ["group"]

    return json.dumps(selection_classes)
