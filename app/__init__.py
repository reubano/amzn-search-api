# -*- coding: utf-8 -*-
"""
    app
    ~~~

    Provides the flask application

    ###########################################################################
    # WARNING: if running on a a staging server, you MUST set the 'STAGE' env
    # heroku config:set STAGE=true --remote staging
    ###########################################################################
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import config

from os import getenv
from json import dumps
from functools import partial

from flask import Flask, send_from_directory, render_template
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_sslify import SSLify

from app.frs import Swaggerify
from app.helper import gen_tables

from builtins import *  # noqa  # pylint: disable=unused-import

__version__ = '1.4.2'

__title__ = 'AMZN Search API'
__package_name__ = 'amzn-search-api'
__author__ = 'Reuben Cummings'
__description__ = 'RESTful API for searching Amazon sites'
__email__ = 'reubano@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 Reuben Cummings'

cache = Cache()
compress = Compress()
swag = Swaggerify()

CACHE_RESULT = [{'name': 'objects', 'desc': 'Success message', 'type': 'str'}]
LOREM_RESULT = [{'name': 'objects', 'desc': 'Bacon sentence', 'type': 'str'}]
SEARCH_RESULT = [
    {
        'name': 'asin', 'desc': 'Amazon Standard Identification Number',
        'type': 'str'},
    {'name': 'country', 'desc': 'Amazon site country', 'type': 'str'},
    {'name': 'currency', 'desc': 'Currency', 'type': 'str'},
    {'name': 'model', 'desc': 'Model number', 'type': 'str'},
    {'name': 'price', 'desc': 'Amazon price', 'type': 'float'},
    {'name': 'sales_rank', 'desc': 'Amazon sales rank', 'type': 'str'},
    {'name': 'title', 'desc': 'Item title', 'type': 'str'},
    {'name': 'url', 'desc': 'Affliate link', 'type': 'str'},
]


def create_app(config_mode=None, config_file=None):
    # Create webapp instance
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    CORS(app)
    compress.init_app(app)
    cache_config = {}

    if config_mode:
        app.config.from_object(getattr(config, config_mode))
    elif config_file:
        app.config.from_pyfile(config_file)
    else:
        app.config.from_envvar('APP_SETTINGS', silent=True)

    if app.config.get('SERVER_NAME'):
        SSLify(app)

    if app.config['HEROKU']:
        cache_config['CACHE_TYPE'] = 'saslmemcached'
        cache_config['CACHE_MEMCACHED_SERVERS'] = [getenv('MEMCACHIER_SERVERS')]
        cache_config['CACHE_MEMCACHED_USERNAME'] = getenv('MEMCACHIER_USERNAME')
        cache_config['CACHE_MEMCACHED_PASSWORD'] = getenv('MEMCACHIER_PASSWORD')
    elif app.config['DEBUG_MEMCACHE']:
        cache_config['CACHE_TYPE'] = 'memcached'
        cache_config['CACHE_MEMCACHED_SERVERS'] = [getenv('MEMCACHE_SERVERS')]
    else:
        cache_config['CACHE_TYPE'] = 'simple'

    cache.init_app(app, config=cache_config)

    skwargs = {
        'name': app.config['APP_NAME'], 'version': __version__,
        'description': __description__}

    swag.init_app(app, **skwargs)

    swag_config = {
        'dom_id': '#swagger-ui',
        'url': app.config['SWAGGER_JSON'],
        'layout': 'StandaloneLayout'}

    context = {
        'base_url': app.config['SWAGGER_URL'],
        'app_name': app.config['APP_NAME'],
        'config_json': dumps(swag_config)}

    @app.route('/')
    @app.route('/<path>/')
    @app.route('{API_URL_PREFIX}/'.format(**app.config))
    @app.route('{API_URL_PREFIX}/<path>/'.format(**app.config))
    def home(path=None):
        if not path or path == 'index.html':
            return render_template('index.html', **context)
        else:
            return send_from_directory('static', path)

    exclude = app.config['SWAGGER_EXCLUDE_COLUMNS']
    create_docs = partial(swag.create_docs, exclude_columns=exclude)
    create_defs = partial(create_docs, skip_path=True)

    create_defs({'columns': CACHE_RESULT, 'name': 'reset_result'})
    create_defs({'columns': CACHE_RESULT, 'name': 'delete_result'})
    create_defs({'columns': LOREM_RESULT, 'name': 'lorem_result'})
    create_defs({'columns': SEARCH_RESULT, 'name': 'search_result'})

    with app.app_context():
        for table in gen_tables(app.view_functions, **app.config):
            create_docs(table)

    return app


# put at bottom to avoid circular reference errors
from app.views import blueprint  # noqa
