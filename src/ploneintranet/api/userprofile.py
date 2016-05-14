# -*- coding: utf-8 -*-
import string
import random

from Products.CMFPlone.utils import safe_unicode
from zope.component import getMultiAdapter
from z3c.form.interfaces import IValidator
from plone import api as plone_api
from plone.api.exc import InvalidParameterError

from ploneintranet.userprofile.interfaces import IMembershipResolver
from ploneintranet.userprofile.content.userprofile import IUserProfile
from dexterity.membrane.behavior.password import IProvidePasswordsSchema


def get_users(
    context=None,
    full_objects=True,
    **kwargs
):
    """
    List users from catalog, avoiding expensive LDAP lookups.

    :param context: Any content object that will be used to find the
        UserResolver context
    :type context: Content object
    :param full_objects: A switch to indicate if full objects or brains should
        be returned
    :type full_objects: boolean
    :returns: user brains or user objects
    :rtype: iterator
    """
    try:
        mtool = plone_api.portal.get_tool('membrane_tool')
    except InvalidParameterError:
        return []
    if context:
        ms_resolver = get_membership_resolver_context(context)
        if ms_resolver:
            kwargs['exact_getUserName'] = [x for x in ms_resolver.members]
    portal_type = 'ploneintranet.userprofile.userprofile',
    search_results = mtool.searchResults(portal_type=portal_type,
                                         **kwargs)
    if full_objects:
        return (x.getObject() for x in search_results)
    else:
        return (brain for brain in search_results)


def get_users_from_userids_and_groupids(ids=None):
    """
    Given a list of userids and groupids return the set of users

    FIXME this has to be folded into get_users once all groups
    are represented as workspaces.
    """
    acl_users = plone_api.portal.get_tool('acl_users')
    users = {}
    for id in ids:
        group = acl_users.getGroupById(id)
        if group:
            for user in group.getGroupMembers():
                user_ob = acl_users.getUserById(user.getId())
                users[user_ob.getProperty('email')] = user_ob
        else:
            user_ob = acl_users.getUserById(id)
            if user_ob:
                users[user_ob.getProperty('email')] = user_ob
    return users.values()


def get(username):
    """Get a Plone Intranet user profile by username

    :param username: Username of the user profile to be found
    :type username: string
    :returns: User profile matching the given username
    :rtype: `ploneintranet.userprofile.content.userprofile.UserProfile` object
    """
    try:
        profile = list(get_users(
            full_objects=True,
            exact_getUserName=username,
        ))[0]
    except IndexError:
        profile = None
    return profile


def get_current():
    """Get the Plone Intranet user profile
    for the current logged-in user

    :returns: User profile matching the current logged-in user
    :rtype: `ploneintranet.userprofile.content.userprofile.UserProfile` object
    """
    if plone_api.user.is_anonymous():
        return None

    current_member = plone_api.user.get_current()
    username = current_member.getUserName()
    return get(username)


def create(
    username,
    email=None,
    password=None,
    approve=False,
    properties=None
):
    """Create a Plone Intranet user profile.

    :param email: [required] Email for the new user.
    :type email: string
    :param username: Username for the new user. This is required if email
        is not used as a username.
    :type username: string
    :param password: Password for the new user. If it's not set we generate
        a random 12-char alpha-numeric one.
    :type password: string
    :param approve: If True, the user profile will be automatically approved
        and be able to log in.
    :type approve: boolean
    :param properties: User properties to assign to the new user.
    :type properties: dict
    :returns: Newly created user
    :rtype: `ploneintranet.userprofile.content.userprofile.UserProfile` object
    """
    portal = plone_api.portal.get()

    # We have to manually validate the username
    validator = getMultiAdapter(
        (portal, None, None, IUserProfile['username'], None),
        IValidator)
    validator.validate(safe_unicode(username))

    # Generate a random password
    if not password:
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choice(chars) for x in range(12))

    profile_container = portal.contentValues(
        {'portal_type': "ploneintranet.userprofile.userprofilecontainer"}
    )[0]

    if properties is None:
        # Avoids using dict as default for a keyword argument.
        properties = {}

    if 'fullname' in properties:
        # Translate from plone-style 'fullname'
        # to first and last names
        fullname = properties.pop('fullname')
        if ' ' in fullname:
            firstname, lastname = fullname.split(' ', 1)
        else:
            firstname = ''
            lastname = fullname
        properties['first_name'] = firstname
        properties['last_name'] = lastname

    profile = plone_api.content.create(
        container=profile_container,
        type='ploneintranet.userprofile.userprofile',
        id=username,
        username=username,
        email=email,
        **properties)

    # We need to manually set the password via the behaviour
    IProvidePasswordsSchema(profile).password = password

    if approve:
        plone_api.content.transition(profile, 'approve')
        profile.reindexObject()

    return profile


def avatar_url(username=None):
    """Get the avatar image url for a user profile

    :param username: Username for which to get the avatar url
    :type username: string
    :returns: absolute url for the avatar image
    :rtype: string
    """
    portal = plone_api.portal.get()
    return '{0}/@@avatars/{1}'.format(
        portal.absolute_url(),
        username,
    )


def get_membership_resolver_context(
    context,
):
    """Get the membership resolver context

    :param context: [required] The context for which
        we want the membership resolver context.
        Can be None.
    :type context: object

    :returns: membership resolver context
    :rtype: object
    """
    if context is None:
        return None

    # context is part of context.aq_chain
    # but unittests do not always wrap acquisition
    resolver = IMembershipResolver(context, None)
    if resolver:
        return resolver
    try:
        chain = context.aq_inner.aq_chain
    except AttributeError:
        return None

    for item in chain:
        resolver = IMembershipResolver(item, None)
        if resolver:
            return resolver
    else:
        return None
