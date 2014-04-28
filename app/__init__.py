# -*- coding: utf-8 -*-
"""
	app
	~~~~~~~~~~~~~~

	Provides the flask application
"""
import config

from os import getenv
from json import JSONEncoder, dumps
from api import Amazon
from amazon.api import SearchException
from flask import Flask, redirect, url_for, request, make_response
from flask.ext.cache import Cache

cache = Cache()
search_cache_timeout = 1 * 60 * 60  # hours (in seconds)


def jsonify(status=200, indent=2, sort_keys=True, **kwargs):
	options = {'indent': indent, 'sort_keys': sort_keys}
	response = make_response(dumps(kwargs, cls=CustomEncoder, **options))
	response.headers['Content-Type'] = 'application/json; charset=utf-8'
	response.headers['mimetype'] = 'application/json'
	response.status_code = status
	return response


def corsify(response, methods):
	base = 'HEAD, OPTIONS'
	headers = 'Origin, X-Requested-With, Content-Type, Accept'

	for m in methods:
		base += ', %s' % m

	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Methods'] = base
	response.headers['Access-Control-Allow-Headers'] = headers
	response.headers['Access-Control-Allow-Credentials'] = 'true'
	return response


def make_cache_key(*args, **kwargs):
	return request.url


def create_app(config_mode=None, config_file=None):
	# Create webapp instance
	app = Flask(__name__)
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

	@app.route('/')
	def home():
		return redirect(url_for('api'))

	@app.route('/api/')
	@app.route('%s/' % app.config['API_URL_PREFIX'])
	def api():
		return 'Welcome to the %s!' % app.config['APP_NAME']

	@app.route('/api/search/')
	@app.route('%s/search/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=search_cache_timeout, key_prefix=make_cache_key)
	def search():
		kwargs = request.args.to_dict()
		limit = int(kwargs.pop('limit', 1))
		amazon = Amazon(**kwargs)

		new = {
			'Condition': 'New',
			'SearchIndex': 'All',
			'ResponseGroup': 'Medium',
		}

		kwargs.update(new)

		try:
			response = amazon.search_n(limit, **kwargs)
			result = amazon.parse(response)
			status = 200
		except SearchException as err:
			result = err.message
			status = 500

		return jsonify(status, objects=result)

	@app.route('/api/reset/')
	@app.route('%s/reset/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=search_cache_timeout)
	def reset():
		cache.clear()
		return jsonify(objects="Caches reset")

	@app.after_request
	def add_cors_header(response):
		return corsify(response, app.config['API_METHODS'])

	return app


class CustomEncoder(JSONEncoder):
	def default(self, obj):
		if set(['quantize', 'year']).intersection(dir(obj)):
			return str(obj)
		elif set(['next', 'union']).intersection(dir(obj)):
			return list(obj)
		return JSONEncoder.default(self, obj)
