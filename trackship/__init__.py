#
import yaml
import logging

config = None
LOG = logging.getLogger('trackship')


def _load_config():
    global config
    try:
        with open('config.yaml') as f:
            config = yaml.load(f)
    except FileNotFoundError:
        LOG.error('Configuration file not found!')

    return config


def _load_importer(name):
    from trackship.importers import amazon
    imp = amazon.Importer()
    return imp


def run():
    # TODO: Dynamic loading of importers
    global config
    LOG.setLevel('DEBUG')

    imp = _load_importer('amazon')
    imp.list_orders()


_load_config()
