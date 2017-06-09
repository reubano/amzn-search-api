# -*- coding: utf-8 -*-
"""
    app
    ~~~~~~~~~~~~~~

    Provides the flask application
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import config

from os import getenv
from inspect import getdoc
from json import JSONEncoder, dumps
from functools import partial
from random import choice

try:
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import HTTPError

from amazon.api import SearchException

from flask import (
    Flask, make_response, send_from_directory, render_template, request)

from flask_cache import Cache
from flask_cors import CORS

from app.api import Amazon
from app.frs import Swaggerify
from app.doc_parser import gen_fields, parse_docblock

from builtins import *  # pylint: disable=F401

__version__ = '1.3.0'

__title__ = config.__APP_NAME__
__package_name__ = 'amzn-search-api'
__author__ = 'Reuben Cummings'
__description__ = 'RESTful API for searching Amazon sites'
__email__ = 'reubano@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 Reuben Cummings'

cache = Cache()
swag = Swaggerify()
search_cache_timeout = 1 * 60 * 60  # hours (in seconds)


# https://baconipsum.com/?paras=5&type=meat-and-filler&make-it-spicy=1
BACON_IPSUM = [
    'Spicy jalapeno bacon ipsum dolor amet prosciutto bresaola ball chicken.',
    'Alcatra officia enim, labore eiusmod kielbasa pancetta turducken.',
    'Aliqua pork loin picanha turducken proident.',
    'Qui meatloaf fatback cillum meatball tail duis short ribs commodo.',
    'Ball tip non salami meatloaf in, tri-tip dolor filet mignon.',
    'Leberkas tenderloin ball tip sirloin, ad culpa drumstick laborum.',
    'Porchetta eiusmod pastrami voluptate pig kielbasa jowl occaecat.',
    'Shank landjaeger andouille ea, in drumstick prosciutto bacon excepteur.']


def jsonify(status=200, indent=2, sort_keys=True, **kwargs):
    options = {'indent': indent, 'sort_keys': sort_keys}
    response = make_response(dumps(kwargs, cls=CustomEncoder, **options))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['mimetype'] = 'application/json'
    response.status_code = status
    return response


def make_cache_key(*args, **kwargs):
    return request.url


def create_app(config_mode=None, config_file=None):
    # Create webapp instance
    app = Flask(__name__)
    CORS(app)
    cache_config = {}

    if config_mode:
        app.config.from_object(getattr(config, config_mode))
    elif config_file:
        app.config.from_pyfile(config_file)
    else:
        app.config.from_envvar('APP_SETTINGS', silent=True)

    if app.config['HEROKU']:
        cache_config['CACHE_TYPE'] = 'spreadsaslmemcachedcache'
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
    @app.route('/<path:path>/')
    @app.route('{API_URL_PREFIX}/'.format(**app.config))
    @app.route('{API_URL_PREFIX}/<path:path>/'.format(**app.config))
    def home(path=None):
        if not path or path == 'index.html':
            return render_template('index.html', **context)
        else:
            print('showing {}'.format(path))
            return send_from_directory('static', path)

    @app.route('/search/')
    @app.route('/api/search/')
    @app.route('{API_URL_PREFIX}/search/'.format(**app.config))
    @cache.cached(timeout=search_cache_timeout, key_prefix=make_cache_key)
    def search():
        """Perform an Amazon site search

        Kwargs:
            Keywords (str): The search term(s) (either this or 'Title' required)
            Title (str): The search title (either this or 'Keywords' required)
            region (str): The localized Amazon site to search
                (one of ['US', 'UK'], default: 'US')

            limit (int): Number of results to return (default: 1)
        """
        kwargs = request.args.to_dict()
        limit = int(kwargs.pop('limit', 1))

        extra = {
            'Condition': 'New', 'SearchIndex': 'All', 'ResponseGroup': 'Medium'}

        kwargs.update(extra)
        amazon = Amazon(**kwargs)

        try:
            response = amazon.search_n(limit, **kwargs)
        except SearchException as err:
            result = str(err)
            status = 500
        except HTTPError:
            msg = 'Amazon Associates tag {} is invalid for region {}'
            result = msg.format(amazon.aws_associate_tag, amazon.region)
            status = 503
        except KeyError:
            result = "region '{}' does not exist".format(amazon.region)
            status = 400
        else:
            result = list(amazon.parse(response))
            status = 200

        return jsonify(status, objects=result)

    @app.route('/lorem/')
    @app.route('/api/lorem/')
    @app.route('{API_URL_PREFIX}/lorem/'.format(**app.config))
    @cache.cached(timeout=search_cache_timeout, key_prefix=make_cache_key)
    def lorem():
        """Return a random bacon ipsum sentence

        Return:
            str: A bacon ipsum sentence
        """
        return jsonify(objects=choice(BACON_IPSUM))

    @app.route('/delete/<base>/')
    @app.route('/api/delete/<base>/')
    @app.route('{API_URL_PREFIX}/delete/<base>/'.format(**app.config))
    def delete(base):
        """Delete a cached url

        Args:
            base (str): The cached url to delete
        """
        url = request.url.replace('delete/', '')
        cache.delete(url)
        return jsonify(objects="Key: %s deleted" % url)

    @app.route('/reset/')
    @app.route('/api/reset/')
    @app.route('{API_URL_PREFIX}/reset/'.format(**app.config))
    def reset():
        """Delete all cached urls

        Return:
            str: Caches reset
        """
        cache.clear()
        return jsonify(objects="Caches reset")

    exclude = app.config['SWAGGER_EXCLUDE_COLUMNS']
    create_docs = partial(swag.create_docs, exclude_columns=exclude)

    result = [{'name': 'objects', 'desc': 'Success message', 'type': 'str'}]
    create_docs({'columns': result, 'name': 'reset_result'}, skip_path=True)
    create_docs({'columns': result, 'name': 'delete_result'}, skip_path=True)

    result = [{'name': 'objects', 'desc': 'Bacon sentence', 'type': 'str'}]
    create_docs({'columns': result, 'name': 'lorem_result'}, skip_path=True)

    result = [
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

    create_docs({'columns': result, 'name': 'search_result'}, skip_path=True)

    with app.app_context():
        for func_name, endpoint in app.view_functions.items():
            if func_name not in app.config['SWAGGER_EXCLUDE_ROUTES']:
                try:
                    method = endpoint.view_class.get
                except AttributeError:
                    method = endpoint

                source = getdoc(method)

                if source:
                    tree = parse_docblock(source)

                    table = {
                        'columns': list(gen_fields(tree)),
                        'name': func_name,
                        'desc': next(tree.iter(tag='paragraph')).text,
                        'tag': 'GET',
                        'rtype': '{}_result'.format(func_name),
                        'list': func_name == 'search'}

                    create_docs(table)

    return app


class CustomEncoder(JSONEncoder):
    def default(self, obj):
        if set(['quantize', 'year']).intersection(dir(obj)):
            return str(obj)
        elif set(['next', 'union']).intersection(dir(obj)):
            return list(obj)
        return JSONEncoder.default(self, obj)
