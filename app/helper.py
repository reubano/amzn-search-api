# -*- coding: utf-8 -*-
"""
    app.helper
    ~~~~~~~~~~

    Provides misc helper functions
"""

from inspect import getdoc
from app.doc_parser import gen_fields, parse_docblock


def gen_tables(view_functions, SWAGGER_EXCLUDE_ROUTES=None, **kwargs):
    exclude_routes = SWAGGER_EXCLUDE_ROUTES or {}

    for func_name, endpoint in view_functions.items():
        if func_name.startswith('blueprint'):
            func_name = '.'.join(func_name.split('.')[1:])

        if func_name not in exclude_routes:
            try:
                method = endpoint.view_class.get
            except AttributeError:
                method = endpoint

            source = getdoc(method)

            if source:
                tree = parse_docblock(source)

                yield {
                    'columns': list(gen_fields(tree)),
                    'name': func_name,
                    'desc': next(tree.iter(tag='paragraph')).text,
                    'tag': 'Amazon' if func_name == 'search' else 'Cache',
                    'rtype': '{}_result'.format(func_name),
                    'list': func_name == 'search'}
