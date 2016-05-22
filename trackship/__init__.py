# -*- coding: utf-8 -*-
__author__ = 'nshahzad'

import yaml

config = None


def _load_config():
    global config
    with open('config.yaml') as f:
        config = yaml.load(f)

    return config


def _load_importer(name):
    from trackship.importers import amazon
    imp = amazon.Importer()
    return imp


def run():
    # TODO: Dynamic loading of importers
    imp = _load_importer('amazon')
    imp.list_orders()


_load_config()
