# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import json

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

from operator import itemgetter

import yaml

from flask import jsonify, request, Blueprint
from builtins import *  # pylint: disable=F401

SWAGGER_TYPES = {
    'bool': 'bool',
    'int': 'integer',
    'dec': 'number',
    'float': 'float',
    'str': 'string',
    'date': 'date',
    'datetime': 'date-time',
}

JSON_TYPES = {
    'bool': 'boolean',
    'float': 'number',
    'binary': 'string',
    'date': 'string',
    'date-time': 'string',
}


def get_column_defn(column):
    stype = SWAGGER_TYPES[column['type']]

    if stype in JSON_TYPES:
        column_defn = {'type': JSON_TYPES[stype], 'format': stype}
    else:
        column_defn = {'type': stype}

    return column_defn


class Swaggerify(object):
    swagger = {
        'swagger': '2.0',
        'info': {},
        'tags': [],
        'schemes': ['https', 'http'],
        'basePath': '/',
        'consumes': ['application/json'],
        'produces': ['application/json'],
        'paths': {},
        'definitions': {}
    }

    def __init__(self, app=None, **kwargs):
        self.app = None

        if app is not None:
            self.init_app(app, **kwargs)

    def to_json(self, **kwargs):
        return json.dumps(self.swagger, **kwargs)

    def to_yaml(self, **kwargs):
        return yaml.dump(self.swagger, **kwargs)

    def __str__(self):
        return self.to_json(indent=4)

    @property
    def tags(self):
        return set(tag['name'] for tag in self.swagger['tags'])

    @tags.setter
    def tags(self, value):
        self.swagger['tags'] = value

    @property
    def version(self):
        if 'version' in self.swagger['info']:
            return self.swagger['info']['version']

        return None

    @version.setter
    def version(self, value):
        self.swagger['info']['version'] = value

    @property
    def title(self):
        if 'title' in self.swagger['info']:
            return self.swagger['info']['title']

        return None

    @title.setter
    def title(self, value):
        self.swagger['info']['title'] = value

    @property
    def description(self):
        if 'description' in self.swagger['info']:
            return self.swagger['info']['description']

        return None

    @description.setter
    def description(self, value):
        self.swagger['info']['description'] = value

    def add_path(self, table, **kwargs):
        path = '{0}/{name}'.format(kwargs.get('url_prefix', ''), **table)
        parameters = []

        for column in table['columns']:
            if column['kind'] in {'param', 'type'}:
                param = {'in': 'path', 'required': True}
                path = '{0}/{{{name}}}'.format(path, **column)
            elif column['kind'] in {'keyword', 'kwtype'}:
                param = {'in': 'query'}

            if column['kind'] in {'param', 'keyword', 'type', 'kwtype'}:
                param.update(
                    {'name': column['name'], 'description': column['desc']})

                param.update(get_column_defn(column))
                parameters.append(param)

        self.swagger['paths'][path] = {}
        ref = '#/definitions/{rtype}'.format(**table)

        if table.get('desc'):
            self.swagger['paths'][path]['description'] = table['desc']

        if table.get('list'):
            _schema = {'type': 'array', 'items': {'$ref': ref}}
            schema = {'type': 'object', 'properties': {'objects': _schema}}
        else:
            schema = {'$ref': ref}

        self.swagger['paths'][path]['get'] = {
            'summary': table.get('desc', 'get {name}'.format(**table)),
            'tags': [table['tag']] if table.get('tag') else [],
            'parameters': parameters,
            'responses': {
                200: {
                    'description': '{name} result'.format(**table),
                    'schema': schema}}}

        if table.get('tag') and table['tag'] not in self.tags:
            tag = {
                'name': table['tag'],
                'description': '{tag} operations'.format(**table)}

            self.swagger['tags'].append(tag)

    def add_defn(self, table):
        def_value = {'type': 'object', 'properties': {}}

        for column in sorted(table['columns'], key=itemgetter('name')):
            excluded = column['name'] in self.exclude_columns

            if excluded or column['name'] == 'id':
                continue

            column_defn = get_column_defn(column)

            if column.get('desc'):
                column_defn['description'] = column['desc']

            def_value['properties'][column['name']] = column_defn

        self.swagger['definitions'][table['name']] = def_value

    def init_app(self, app, **kwargs):
        self.app = app
        swagger = Blueprint('swagger', __name__)

        if kwargs.get('name'):
            self.title = kwargs['name']

        if kwargs.get('version'):
            self.version = kwargs['version']

        if kwargs.get('description'):
            self.description = kwargs['description']

        @swagger.route('/swagger.json')
        def swagger_json():
            # Must have a request context
            self.swagger['host'] = urlparse.urlparse(request.url_root).netloc
            return jsonify(self.swagger)

        app.register_blueprint(swagger)

    def create_docs(self, table, **kwargs):
        self.exclude_columns = set(kwargs.get('exclude_columns', []))

        if not kwargs.get('skip_defn'):
            self.add_defn(table)

        if not kwargs.get('skip_path'):
            self.add_path(table, **kwargs)
