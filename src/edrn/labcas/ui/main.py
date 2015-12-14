# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
import sys


def hello_world(request):
    return Response('Hiya %(name)s!' % request.matchdict)


def main(argv=None):
    if argv is None: argv = sys.argv
    config = Configurator()
    config.add_route('hello', '/hello/{name}')
    config.add_view(hello_world, route_name='hello')
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
    return True


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv) else -1)
