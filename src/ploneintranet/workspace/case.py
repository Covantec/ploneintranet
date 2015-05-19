from ploneintranet.attachments.attachments import IAttachmentStoragable
from zope.interface import implementer

import ploneintranet.workspace.workspacefolder
from .workspacefolder import IWorkspaceFolder
from .workspacefolder import WorkspaceFolder


class ICase(IWorkspaceFolder):
    """
    Interface for Case
    """


@implementer(ICase, IAttachmentStoragable)
class Case(WorkspaceFolder):
    """
    A Case users can collaborate on
    """

    @property
    def is_case(self):
        """ XXX remove after case refactoring """
        return True
