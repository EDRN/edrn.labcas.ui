# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from pyramid.view import view_config, view_defaults
from pyramid.response import Response
import os.path, json, httplib, os


@view_defaults(renderer=PACKAGE_NAME + ':templates/accept.pt')
class AcceptView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='accept', permission='upload')
    def __call__(self):
        if u'data' in self.request.params:
            if 'name' not in self.request.params or 'file' not in self.request.params:
                return Response(json.dumps({
                    u'OK': 0,
                    u'info': u'Missing "name" and/or "file" form elements'
                }), httplib.OK, content_type='application/json')
            filename, f = self.request.params['name'], self.request.params['file']
            target = os.path.join(self.request.session['datasetDir'], filename)
            with open(target, 'wb') as out:
                while True:
                    buf = f.file.read(f.bufsize)
                    if len(buf) == 0: break
                    out.write(buf)
            return Response(json.dumps({u'OK': 1}), httplib.OK, content_type='application/json')
        entries = os.listdir(self.request.session['datasetDir'])
        try:
            del entries[entries.index('DatasetMetadata.xmlmet')]
        except ValueError:
            pass
        entries.sort()
        return {
            'hasFiles': len(entries) > 0,
            'currentFiles': entries,
            'metadataForm': self.request.session['metadataForm']
        }
