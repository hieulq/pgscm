from flask_potion.instances import Instances, Pagination
from flask import current_app, json, request
from flask_potion.exceptions import InvalidJSON
from flask_potion.contrib.alchemy import SQLAlchemyManager
import collections


class DataTableSchema(Instances):
    def schema(self):
        request_schema = {
            "type": "object",
            "properties": {
                "where": self._filter_schema,
                "sort": self._sort_schema,
                "start": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0
                },
                "length": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": current_app.config['POTION_MAX_PER_PAGE'],
                    "default": current_app.config['POTION_DEFAULT_PER_PAGE'],
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": current_app.config['POTION_MAX_PER_PAGE'],
                    "default": current_app.config['POTION_DEFAULT_PER_PAGE'],
                }
            },
            "additionalProperties": True
        }

        response_schema = {
            "type": "object",
            "properties": {
                "recordsTotal": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0
                },
                "recordsFiltered": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 0,
                },
                "data": {
                    "type": "array",
                    "items": {
                        "items": {"$ref": "#"}
                    }
                },
                "error": {
                    "type": "string",
                }
            }
        }

        return response_schema, request_schema

    def parse_request(self, request):

        # TODO convert instances to FieldSet
        # TODO (implement in FieldSet too:) load values from request.args
        try:
            page = request.args.get('page', 1, type=int)
            start = request.args.get('start', 1, type=int)
            length = request.args.get('length', current_app.config[
                'POTION_DEFAULT_PER_PAGE'], type=int)
            per_page = request.args.get('per_page', current_app.config[
                'POTION_DEFAULT_PER_PAGE'], type=int)
            where = json.loads(request.args.get('where', '{}'))  # FIXME
            sort = json.loads(request.args.get('sort', '{}'),
                              object_pairs_hook=collections.OrderedDict)
        except ValueError:
            raise InvalidJSON()

        result = self.convert({
            "page": page,
            "start": start + 1,  # convert from datatable paging to potion page
            "length": length,
            "per_page": per_page,
            "where": where,
            "sort": sort
        })

        result['where'] = tuple(self._convert_filters(result['where']))
        result['sort'] = tuple(self._convert_sort(result['sort']))
        return result

    def format_response(self, data):
        if not isinstance(data, self._pagination_types):
            return self.format(data)

        links = [(request.path, data.page, data.per_page, 'self')]

        if data.has_prev:
            links.append((request.path, 1, data.per_page, 'first'))
            links.append((request.path, data.page - 1, data.per_page, 'prev'))
        if data.has_next:
            links.append((request.path, data.page + 1, data.per_page, 'next'))

        links.append((request.path, max(data.pages, 1), data.per_page, 'last'))

        # FIXME links must contain filters & sort
        # TODO include query_params

        headers = {
            'Link': ','.join(('<{0}?page={1}&per_page={2}>; rel="{3}"'.
                             format(*link) for link in links)),
            'X-Total-Count': data.total
        }
        res = dict()
        res['draw'] = 1
        res['recordsTotal'] = data.total
        res['recordsFiltered'] = data.total
        res['data'] = self.format(data.items)

        return res, 200, headers


class PgsResourceManager(SQLAlchemyManager):

    def paginated_instances_dt(self, page, per_page, start, length,
                               where=None, sort=None):
        instances = self.instances(where=where, sort=sort)
        if isinstance(instances, list):
            return Pagination.from_list(instances, start, length)
        return self._query_get_paginated_items(instances, start, length)
