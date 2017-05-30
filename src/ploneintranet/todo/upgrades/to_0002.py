# coding=utf-8
from plone import api
from ploneintranet.todo.setuphandlers import create_app


def create_todo_app(context):
    ''' Create the todo app if it is not there or if it is a dummy one
    '''
    portal = api.portal.get()
    apps = portal.apps
    app = apps['todo']
    if app:
        if not app.app:
            # Once there was a placeholder for the todo app that had app = None
            # We remove it before installing the newly provided one
            api.content.delete(app)
        else:
            # If the app is not the dummy one, do not do anything
            return
    create_app()
