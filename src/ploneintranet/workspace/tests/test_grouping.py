from plone.app.linkintegrity.info import IUUID
from plone.app.testing import login
from plone.app.testing.interfaces import TEST_USER_NAME
from plone.app.testing.interfaces import SITE_OWNER_NAME
from staralliance.theme.groupings import IGroupingStorage
from staralliance.theme.testing import STARALLIANCE_THEME_INTEGRATION_TESTING
import unittest2 as unittest


class TestGroupingStorage(unittest.TestCase):
    """ Test the IGroupingStorage adapter
    """
    layer = STARALLIANCE_THEME_INTEGRATION_TESTING

    def setUp(self):
        """ """
        portal = self.layer['portal']
        login(self.layer['app'], SITE_OWNER_NAME)
        workspaces = portal.workspaces
        workspaces.invokeFactory(
            'staralliance.types.workspace',
            'workspace',
            title='Workspace')
        self.workspace = workspaces._getOb('workspace')
        self.storage = IGroupingStorage(self.workspace)
        self.groupings = self.storage.get_groupings()

    def tearDown(self):
        portal = self.layer['portal']
        login(self.layer['app'], SITE_OWNER_NAME)
        workspaces = portal.workspaces
        workspaces.manage_delObjects('workspace')
        login(portal, TEST_USER_NAME)

    def test_groupings(self):
        """ """
        login(self.layer['app'], SITE_OWNER_NAME)
        self.assertEqual(
            sorted([k for k in self.groupings.keys()]),
            sorted(['label', 'author', 'type']))

    def test_label_groupings(self):
        """ Test that IGroupingStorage is correctly updated when labels change
        """
        self.assertEqual(len(self.groupings['label'].keys()), 0)

        # Create a new object, give it a label and check that this object's
        # data appears under that label in IGroupingStorage
        tid = self.workspace.invokeFactory('File', 'File', title='File')
        obj1 = self.workspace._getOb(tid)
        obj1.setSubject('foo')
        self.storage.update_groupings(obj1)  # Update IGroupingStorage
        self.assertEqual(
            [f for f in self.groupings['label'].keys()],
            ['foo'])

        obj1.setSubject(['bar', 'foo'])
        self.storage.update_groupings(obj1)
        self.assertEqual(
            sorted([f for f in self.groupings['label'].keys()]),
            sorted(['foo', 'bar']))

        self.assertEqual(len(self.groupings['label']['foo']), 1)
        self.assertEqual(len(self.groupings['label']['bar']), 1)
        self.assertEqual(
            list(self.groupings['label']['foo'].uids)[0], IUUID(obj1))
        self.assertEqual(
            list(self.groupings['label']['bar'].uids)[0], IUUID(obj1))

        # Set another label and test
        obj1.setSubject('bar')
        self.storage.update_groupings(obj1)
        self.assertEqual([f for f in self.groupings['label'].keys()], ['bar'])

        # Create another object and check again
        tid = self.workspace.invokeFactory(
            'Document', 'Document', title='Document')
        obj2 = self.workspace._getOb(tid)
        obj2.setSubject('bar')
        self.storage.update_groupings(obj2)  # Update IGroupingStorage
        self.assertEqual(len(self.groupings['label']['bar']), 2)
        self.assertEqual(
            sorted(list(self.groupings['label']['bar'].uids)),
            sorted([IUUID(obj1), IUUID(obj2)]))

        # Check that objects are succesfully removed from IGroupingStorage
        self.storage.remove_from_groupings(obj1)
        self.assertEqual(len(self.groupings['label']['bar']), 1)
        self.storage.remove_from_groupings(obj2)
        self.assertEqual(len(self.groupings['label'].keys()), 0)

    def test_author_groupings(self):
        """ Test that IGroupingStorage's author info is correctly updated
        """
        self.assertEqual(len(self.groupings['author'].keys()), 0)

        tid = self.workspace.invokeFactory('File', 'File1', title='File')
        obj1 = self.workspace._getOb(tid)
        obj1.setSubject('foo')
        self.storage.update_groupings(obj1)  # Update IGroupingStorage
        self.assertEqual(
            [f for f in self.groupings['author'].keys()],
            [SITE_OWNER_NAME])

    def test_type_groupings(self):
        """ Test that IGroupingStorage's type info is correctly updated
        """
        self.assertEqual(len(self.groupings['type'].keys()), 0)

        tid = self.workspace.invokeFactory('File', 'File1', title='File')
        obj1 = self.workspace._getOb(tid)
        obj1.documentType = ('baz',)
        self.storage.update_groupings(obj1)  # Update IGroupingStorage
        self.assertEqual([f for f in self.groupings['type'].keys()], ['baz'])

    def test_ordering(self):
        """ Groupings can be ordered arbitrarily by users. Test that this
            works.
        """
        self.assertEqual(len(self.groupings['author'].keys()), 0)
        self.assertEqual(self.storage.get_order_for('label'), [])

        tid = self.workspace.invokeFactory('File', 'File', title='File')
        file = self.workspace._getOb(tid)
        file.setSubject('foo')
        self.storage.update_groupings(file)  # Update IGroupingStorage
        self.assertEqual(self.storage.get_order_for('label'),
                         [{'archived': False, 'heading': 'foo'}])

        file.setSubject(('foo', 'bar'))
        self.storage.update_groupings(file)
        self.assertEqual(
            self.storage.get_order_for('label'),
            [dict(heading=g, archived=False) for g in ['foo', 'bar']])

        tid = self.workspace.invokeFactory(
            'Document', 'Document', title='Document')
        doc = self.workspace._getOb(tid)
        doc.setSubject(('foo', 'bar', 'baz'))
        self.storage.update_groupings(doc)
        self.assertEqual(
            self.storage.get_order_for('label'),
            [dict(heading=g, archived=False) for g in ['foo', 'bar', 'baz']])

        # Set a custom order and test
        self.storage.set_order_for('label', ['bar', 'baz', 'foo'])
        self.assertEqual(
            self.storage.get_order_for('label'),
            [dict(heading=g, archived=False) for g in ['bar', 'baz', 'foo']])

        # Set a custom order and test
        self.storage.set_order_for('label', ['foo', 'bar', 'baz'])
        self.assertEqual(
            self.storage.get_order_for('label'),
            [dict(heading=g, archived=False) for g in ['foo', 'bar', 'baz']])

        self.assertEqual(
            self.storage.get_order_for('label', alphabetical=True),
            [dict(heading=g, archived=False) for g in ['bar', 'baz', 'foo']])

        self.storage.reset_order()  # Resets to alphabetical order
        self.assertEqual(
            self.storage.get_order_for('label'),
            [dict(heading=g, archived=False) for g in ['bar', 'baz', 'foo']])

    def test_archiving(self):
        """ In the case of labels (i.e. tags), individual grouping values can
            be archived.
        """
        tid = self.workspace.invokeFactory('File', 'File', title='File')
        file = self.workspace._getOb(tid)
        file.setSubject(('foo', 'bar'))
        self.storage.update_groupings(file)

        tid = self.workspace.invokeFactory(
            'Document', 'Document', title='Document')
        doc = self.workspace._getOb(tid)
        doc.setSubject(('bar', 'baz', 'buz'))
        self.storage.update_groupings(doc)

        tid = self.workspace.invokeFactory('Link', 'Link', title='Link')
        link = self.workspace._getOb(tid)
        link.setSubject(('baz'))
        self.storage.update_groupings(link)

        self.assertEqual(
            self.storage.get_order_for(
                'label',
                alphabetical=True),
            [dict(heading=g, archived=False) for g in
                ['bar', 'baz', 'buz', 'foo']])

        groupings = self.storage.get_groupings()
        groupings['label'].get('buz').archived = True

        self.assertEqual(
            self.storage.get_order_for(
                'label',
                alphabetical=True),
            [dict(heading=g, archived=False) for g in
                ['bar', 'baz', 'foo']])

        self.assertEqual(
            self.storage.get_order_for(
                'label',
                include_archived=True,
                alphabetical=True),
            [dict(heading=g, archived=g == 'buz') for g in
                ['bar', 'baz', 'buz', 'foo']])
