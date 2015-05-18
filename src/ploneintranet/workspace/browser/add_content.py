# -*- coding: utf-8 -*-
from Products.CMFPlacefulWorkflow.PlacefulWorkflowTool import \
    WorkflowPolicyConfig_id
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.utilities.marker import mark
from plone import api
from plone.namedfile.file import NamedBlobImage
from ploneintranet.workspace.interfaces import ICase


class AddContent(BrowserView):
    """Evaluate simple form and add arbitrary content.
    """

    template = ViewPageTemplateFile('templates/add_content.pt')

    def __call__(
            self,
            portal_type=None,
            title=None,
            description=None,
            image=None,
            workspace_type=None,
            workflow=None):
        """Evaluate form and redirect"""
        if title is not None:
            self.portal_type = portal_type.strip()
            self.title = title.strip()
            self.description = description.strip()
            self.image = image
            if workspace_type:
                self.workspace_type = workspace_type.strip()
            if workflow:
                self.workflow = workflow.strip()
            if self.portal_type in api.portal.get_tool('portal_types'):
                url = self.create(image)
                return self.redirect(url)
        return self.template()

    def create(self, image=None):
        """Create content and return url. In case of images add the image."""
        container = self.context
        new = api.content.create(
            container=container,
            type=self.portal_type,
            title=self.title,
            safe_id=True,
        )
        if image:
            namedblobimage = NamedBlobImage(
                data=image.read(),
                filename=safe_unicode(image.filename))
            new.image = namedblobimage

        if new:
            new.description = safe_unicode(self.description)
            if getattr(self, 'workspace_type', '') == 'workspace-workflow':
                mark(new, ICase)
                policy = getattr(new, WorkflowPolicyConfig_id)
                policy.setPolicyIn("case_workflow")
            return new.absolute_url()

    def redirect(self, url):
        """Has its own method to allow overriding"""
        url = '{}/view'.format(url)
        return self.request.response.redirect(url)


class AddFolder(AddContent):

    template = ViewPageTemplateFile('templates/add_folder.pt')


class AddTask(AddContent):

    template = ViewPageTemplateFile('templates/add_task.pt')
