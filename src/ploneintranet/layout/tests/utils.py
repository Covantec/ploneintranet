# coding=utf-8
from plone.app.contenttypes.content import Folder
from ploneintranet.layout.app import AbstractAppContainer
from ploneintranet.layout.interfaces import IAppContainer
from ploneintranet.layout.interfaces import IAppLayer
from ploneintranet.layout.interfaces import IAppView
from ploneintranet.layout.layers import get_layers
from Products.Five import BrowserView
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse


class IMockLayer(IAppLayer):
    pass


class IMockFolder(IAppContainer):
    pass


class MockFolder(AbstractAppContainer, Folder):
    """A mock folder that inherits the app registration hook
    from AbstractAppContainer."""
    implements(IMockFolder)

    app_name = 'mock'
    app_layers = (IMockLayer, )

    # def __init__(self, *args, **kwargs):
    #     super(MockFolder, self).__init__(*args, **kwargs)
    #     self.register_app_hook()


class AppTestingView(BrowserView):
    """ A mock View that represents an App in the Apps space """
    implements(IPublishTraverse, IAppView)
    app_name = 'testing'


class LayersView(BrowserView):

    def __call__(self):
        layers = '\n'.join([str(layer) for layer in get_layers(self.request)])
        req_items = '\n'.join([str(i) for i in self.request.items()])
        return "%s\n\n%s" % (layers, req_items)
