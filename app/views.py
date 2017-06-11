# -*- coding: utf-8 -*-
"""
    app.view
    ~~~~~~~~

    Provides additional api endpoints
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from random import choice

try:
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import HTTPError

from amazon.api import SearchException
from flask import Blueprint, request

from config import Config

from app import cache
from app.api import Amazon
from app.utils import make_cache_key, jsonify, BACON_IPSUM, cache_header

from builtins import *  # noqa  # pylint: disable=unused-import

blueprint = Blueprint('blueprint', __name__)

PREFIX = Config.API_URL_PREFIX
CACHE_TIMEOUT = Config.CACHE_TIMEOUT


# API routes
@blueprint.route('/search/')
@blueprint.route('/api/search/')
@blueprint.route('{}/search/'.format(PREFIX))
@cache_header(CACHE_TIMEOUT, key_prefix=make_cache_key)
def search():
    """Perform an Amazon site search

    Kwargs:
        q (str): The search term (required)


        region (str): The localized Amazon site to search
            (one of ['US', 'UK'], default: 'US')

        limit (int): Number of results to return (default: 1)
    """
    kwargs = request.args.to_dict()
    kwargs.setdefault('Keywords', kwargs.pop('q', None))
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


# Cache routes
@blueprint.route('/lorem/')
@blueprint.route('/api/lorem/')
@blueprint.route('{}/lorem/'.format(PREFIX))
@cache_header(CACHE_TIMEOUT, key_prefix=make_cache_key)
def lorem():
    """Return a random bacon ipsum sentence

    Return:
        str: A bacon ipsum sentence
    """
    return jsonify(objects=choice(BACON_IPSUM))


@blueprint.route('/delete/<base>/')
@blueprint.route('/api/delete/<base>/')
@blueprint.route('{}/delete/<base>/'.format(PREFIX))
def delete(base):
    """Delete a cached url

    Args:
        base (str): The base of the cached url to delete
    """
    url = request.url.replace('delete/', '')
    cache.delete(url)
    return jsonify(objects='Key: {} deleted'.format(url))


@blueprint.route('/reset/')
@blueprint.route('/api/reset/')
@blueprint.route('{}/reset/'.format(PREFIX))
def reset():
    """Delete all cached urls

    Return:
        str: Caches reset
    """
    cache.clear()
    return jsonify(objects='Caches reset')
