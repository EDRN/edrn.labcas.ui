# encoding: utf-8
#
# Main command for Docker

from pyramid.scripts.pserve import main as pserve_main
import os, os.path, subprocess, logging


logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)
_settings = '/app/persistence/settings'
_updater = '/usr/local/bin/update-settings'
_ingestor = '/usr/local/bin/update-vocabularies'


def main():
    _logger.info('Checking sentinel file %s', _settings)
    if not os.path.isfile(_settings):
        try:
            _logger.info('Sentinel file not found, so calling %s', _updater)
            results = subprocess.check_output([_updater], stderr=subprocess.STDOUT)
            _logger.debug('Results from update-settings: %s', results)
            _logger.info("And don't forget to call %s, too'", _ingestor)
            # TODO: call this
            # subprocess.check_call([_ingestor])
        except subprocess.CalledProcessError as ex:
            _logger.exception('Failed setup')
    else:
        _logger.info('Initial setup already complete')
    _logger.info('Starting pyramid app')
    pserve_main(['app', '/app/persistence/paste.cfg'])


if __name__ == '__main__':
    main()
