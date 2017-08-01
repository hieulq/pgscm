#!/usr/bin/env python
# coding=utf8

__version__ = '2.3.3'

import re

from jinja2 import Markup
from flask import Blueprint, current_app, url_for, g


class CDN(object):
    """Base class for CDN objects."""

    def get_resource_url(self, filename):
        """Return resource url for filename."""
        raise NotImplementedError


class StaticCDN(object):
    """A CDN that serves content from the local application.

    :param static_endpoint: Endpoint to use.
    :param rev: If ``True``, honor ``ADMINLTE_QUERYSTRING_REVVING``.
    """

    def __init__(self, static_endpoint='static', rev=False):
        self.static_endpoint = static_endpoint
        self.rev = rev

    def get_resource_url(self, filename):
        extra_args = {}

        if self.rev and current_app.config['ADMINLTE_QUERYSTRING_REVVING']:
            extra_args['adminlte'] = __version__

        return url_for(self.static_endpoint, filename=filename, **extra_args)


class WebCDN(object):
    """Serves files from the Web.

    :param baseurl: The baseurl. Filenames are simply appended to this URL.
    """

    def __init__(self, baseurl):
        self.baseurl = baseurl

    def get_resource_url(self, filename):
        return self.baseurl + filename


class ConditionalCDN(object):
    """Serves files from one CDN or another, depending on whether a
    configuration value is set.

    :param confvar: Configuration variable to use.
    :param primary: CDN to use if the configuration variable is ``True``.
    :param fallback: CDN to use otherwise.
    """

    def __init__(self, confvar, primary, fallback):
        self.confvar = confvar
        self.primary = primary
        self.fallback = fallback

    def get_resource_url(self, filename):
        if current_app.config[self.confvar]:
            return self.primary.get_resource_url(filename)
        return self.fallback.get_resource_url(filename)


def adminlte_find_resource(filename, cdn, use_minified=None, local=True):
    """Resource finding function, also available in templates.

    Tries to find a resource, will force SSL depending on
    ``ADMINLTE_CDN_FORCE_SSL`` settings.

    :param filename: File to find a URL for.
    :param cdn: Name of the CDN to use.
    :param use_minified': If set to ``True``/``False``, use/don't use
                          minified. If ``None``, honors
                          ``ADMINLTE_USE_MINIFIED``.
    :param local: If ``True``, uses the ``local``-CDN when
                  ``ADMINLTE_SERVE_LOCAL`` is enabled. If ``False``, uses
                  the ``static``-CDN instead.
    :return: A URL.
    """
    config = current_app.config

    if use_minified is None:
        use_minified = config['ADMINLTE_USE_MINIFIED']

    if use_minified:
        filename = '%s.min.%s' % tuple(filename.rsplit('.', 1))

    cdns = current_app.extensions['adminlte']['cdns']
    resource_url = cdns[cdn].get_resource_url(filename)

    if resource_url.startswith('//') and config['ADMINLTE_CDN_FORCE_SSL']:
        resource_url = 'https:%s' % resource_url

    return resource_url


def is_active_in_tree(request, endpoint, tree=True):
    if endpoint == request.endpoint[:-3]:
        return 'active'
    elif tree:
        return 'treeview'
    else:
        return 'node'


def load_datatables_script(ajax_endpoint="", export_columns="",
                           column_names=[], js=True, select2_class=None):
    if js:
        select2_script = ""
        datatables_script = """
        <script src="{0}"></script>
        <script src="{1}"></script>
        <script src="{2}"></script>
        <script src="{3}"></script>
        <script src="{4}"></script>
        <script src="{5}"></script>
        <script src="{6}"></script>
        <script src="{7}"></script>
        <script src="{8}"></script>
        """.format(
            adminlte_find_resource('js/plugins/datatables/jquery.dataTables.js',  # noqa
                                   cdn='local', use_minified=False),
            adminlte_find_resource('js/plugins/datatables/dataTables.bootstrap.js',  # noqa
                                   cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/dataTables.buttons.js',  # noqa
                cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/buttons.bootstrap.js',  # noqa
                cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/buttons.print.js',
                cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/buttons.html5.js',
                cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/jszip.js',
                cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/pdfmake.js',
                cdn='local', use_minified=True),
            adminlte_find_resource(
                'js/plugins/datatables/extensions/Buttons/js/vfs_fonts.js',
                cdn='local', use_minified=False)
        )
        if select2_class:
            datatables_script += """
                <script src="{0}"></script>
                """.format(
                adminlte_find_resource(
                    'js/plugins/select2/select2.js',
                    cdn='local', use_minified=True))
            select2_script = """$(".{0}").select2({{width: '100%'}});""". \
                format(select2_class)

        if current_app.config['AJAX_CALL_ENABLED']:
            mapping = ""
            for column in column_names:
                mapping += """{{ "data": "{0}", "orderable": {1}, "searchable": {1} }},
                """.format(column[0], str(column[1]).lower())

            server_script = """
            "serverSide": true,
            "ajax": function(data, callback, settings) {{
                var sort_column_name = data.columns[data.order[0].column].data;
                var direction = data.order[0].dir == 'asc' ? true : false
                var where_params = {{}}
                var sort_params = {{}}
                sort_params[sort_column_name] = direction; 
                if (data.search.value) {{
                    for (idx in data.columns) {{
                        if (data.columns[idx].searchable) {{
                            where_params[data.columns[idx].data] = {{}};
                            where_params[data.columns[idx].data]["$contains"]=data.search.value;
                        }}
                    }}
                }};
                $.get('/{0}', {{
                    per_page: data.length,
                    page: data.start + 1,
                    where: JSON.stringify(where_params),
                    sort: JSON.stringify(sort_params)
                    }}, 
                    function(res, status, req) {{
                        callback({{
                            recordsTotal: req.getResponseHeader('X-Total-Count'),
                            recordsFiltered: res.length,
                            data: res
                            }});
                    }});
            }},
            "columns": [
                {1}
            ],
            """.format(ajax_endpoint, mapping)
        else:
            server_script = """
            "serverSide": false,
            """
        script = Markup("""
        {0}
        <!-- page script -->
        <script>
            $(function () {{
                var table = $('#pgs_data').DataTable({{
                    "language": {{
                        "url": "/static/{1}.json"
                    }},
                    buttons: [
                        {{
                            extend: 'excelHtml5',
                            text: '<i class="fa fa-file-excel-o"></i>',
                            titleAttr: 'Excel',
                            exportOptions: {{
                                columns: [{2}]
                            }}
                        }},
                        {{
                            extend: 'pdfHtml5',
                            text: '<i class="fa fa-file-pdf-o"></i>',
                            titleAttr: 'PDF',
                            exportOptions: {{
                                columns: [{2}]
                            }}
                        }},
                        {{
                            extend: 'print',
                            text: '<i class="fa fa-print"></i>',
                            titleAttr: 'Print',
                            exportOptions: {{
                                columns: [{2}]
                            }}
                        }}
                    ],
                    "processing": true,
                    {3}
                    "paging": true,
                    "pagingType": "full_numbers",
                    "lengthChange": true,
                    "searching": true,
                    "ordering": true,
                    "info": true,
                    "autoWidth": true,
                    "initComplete": function (settings, json) {{
                        $('.{7}').appendTo('#pgs_data_filter');
                        table.buttons().container().appendTo('#pgs_data_filter');
                        $('.dt-buttons').css("margin-left", "5px")
                        $('.{7}').css("margin-left", "5px");
                    }},
                }})
                $('.{4}').on('click', function (event) {{
                    var data = $(this).data()
                    var modal = $('#{5}')
                    for (var key in data) {{
                        var target = modal.find('#' + key)
                        value = ''
                        if (data[key]!='None'){{value = data[key]}}
                        if (target.is('select')){{
                            target.val(data[key])
                        }} else {{
                            modal.find('#' + key).val(value)
                        }}
                    }}
                }})
                {6}
                $('.{8}').on('click', function (event) {{
                    var data = $(this).data()
                    var modal_del = $('#{9}')
                    modal_del.find('#id').val(data['id'])
                }})
                $('.{10}').parent()
                .append('<button type="button" class="btn btn-default"'+
                 'data-dismiss="modal">Cancel</button>')

                $('.{10}').removeClass('btn-default')
                .addClass('btn-primary pull-right')
                .before("<hr />" )
                
                $('#{11}').removeClass('btn-primary')
                .addClass('btn-warning')

            }});
        </script>
        """.format(datatables_script, g.language,
                   export_columns, server_script, g.c.BTNEDIT_ID,
                   g.c.MODAL_EDIT_ID, select2_script, g.c.BTNADD_ID,
                   g.c.BTNDEL_ID, g.c.MODAL_DEL_ID, g.c.SUBMIT_DEFAULT_CLASS,
                   g.c.DEL_SUBMIT_ID))
        return script
    else:
        css_script = """
            <link href="{0}" rel="stylesheet" type="text/css">
                """.format(adminlte_find_resource(
            'js/plugins/datatables/dataTables.bootstrap.css', cdn='local',
            use_minified=True))
        if select2_class:
            css_script += """
            <link href="{0}" rel="stylesheet" type="text/css">
                """.format(adminlte_find_resource(
                'js/plugins/select2/select2.css', cdn='local',
                use_minified=True))
        return Markup(css_script)


def check_role(current, target):
    for role in current:
        if role in target:
            return True
    return False


def breadcrumb_gen():
    pass


class AdminLTE(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        ADMINLTE_VERSION = re.sub(r'^(\d+\.\d+\.\d+).*', r'\1', __version__)
        JQUERY_VERSION = '2.1.4'
        HTML5SHIV_VERSION = '3.7.0'
        RESPONDJS_VERSION = '1.3.0'

        app.config.setdefault('ADMINLTE_USE_MINIFIED', True)
        app.config.setdefault('ADMINLTE_CDN_FORCE_SSL', False)

        app.config.setdefault('ADMINLTE_QUERYSTRING_REVVING', True)
        app.config.setdefault('ADMINLTE_SERVE_LOCAL', False)

        blueprint = Blueprint(
            'adminlte',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=app.static_url_path + '/adminlte')

        app.register_blueprint(blueprint)

        app.jinja_env.globals['adminlte_find_resource'] = \
            adminlte_find_resource
        app.jinja_env.globals['is_active_in_tree'] = \
            is_active_in_tree
        app.jinja_env.globals['check_role'] = \
            check_role
        app.jinja_env.globals['load_datatables_script'] = \
            load_datatables_script

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        local = StaticCDN('adminlte.static', rev=True)
        static = StaticCDN()

        def lwrap(cdn, primary=static):
            return ConditionalCDN('ADMINLTE_SERVE_LOCAL', primary, cdn)

        bootstrap = lwrap(
            WebCDN('//cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/%s/'
                   % ADMINLTE_VERSION),
            local)

        jquery = lwrap(
            WebCDN('//cdnjs.cloudflare.com/ajax/libs/jquery/%s/'
                   % JQUERY_VERSION),
            local)

        html5shiv = lwrap(
            WebCDN('//cdnjs.cloudflare.com/ajax/libs/html5shiv/%s/'
                   % HTML5SHIV_VERSION))

        respondjs = lwrap(
            WebCDN('//cdnjs.cloudflare.com/ajax/libs/respond.js/%s/'
                   % RESPONDJS_VERSION))

        app.extensions['adminlte'] = {
            'cdns': {
                'local': local,
                'static': static,
                'bootstrap': bootstrap,
                'jquery': jquery,
                'html5shiv': html5shiv,
                'respond.js': respondjs,
            },
        }
