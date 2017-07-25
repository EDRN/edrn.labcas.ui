# encoding: utf-8

from pyramid.response import FileResponse
import os.path


def favicon_view(request):
    parent = os.path.dirname(os.path.dirname(__file__))
    icon = os.path.join(parent, 'static', 'favicon.ico')
    return FileResponse(icon, request=request)
