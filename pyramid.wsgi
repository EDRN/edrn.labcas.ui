# encoding: utf-8

from pyramid.paster import get_app, setup_logging
ini_path = '/usr/local/labcas/ui/current/production.ini'
setup_logging(ini_path)
application = get_app(ini_path, 'main')
