#!/usr/bin/env python
# coding=utf8

__version__ = '2.3.3'

import re
import json

from jinja2 import Markup
from flask import Blueprint, current_app, url_for, g
from flask_security import current_user
from pgscm.utils import _, is_region_role


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


def _render_btn(id, size='btn-xs', type='btn-default', modal_target='modal', title="", css_class='plus', data=None):
    data_attr = ""
    if data:
        for col in data.__table__.c._data:
            if not col.startswith('_'):
                data_attr += """
                    data-{0} = "{1}"
                """.format(col, data.__getattribute__(col))
    btn = """
    <button type="button" class="btn {0} {1} {2}"
            data-toggle="modal"
            data-target="#{3}"            
            {4}
            >
        <span class="fa fa-{5}"></span>
        {6}
    </button>
    """.format(id, size, type, modal_target, data_attr, css_class, title)
    return btn


def is_active_in_tree(request, endpoint, tree=False):
    if not tree and endpoint == request.endpoint[:-3]:
        return 'active'
    elif tree and endpoint == request.endpoint.split('.')[0]:
        return 'active'
    else:
        return 'node'


def lurl_for(endpoint):
    return url_for(endpoint + '_' + g.language)


def load_datatables_script(ajax_endpoint="", crud_endpoint=[], export_columns="",
                           column_names=[], js=True, select2_class=None, multi_select2_class=None,
                           has_button_view=False):
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
            if multi_select2_class:
                select2_script += """$('.{0}').select2({{width: '100%'}})
                .attr('multiple', 'multiple');
                $('.select2-search__field').css('border', 'none');
                """.format(multi_select2_class)

            if current_user.province_id and is_region_role():
                has_province_id = 1
            else:
                has_province_id = 0

            select2_script += """
                    var select2_elements = $('select')
                    
                    function select2_ajax(i, h, resource){{
                        $.ajax({{
                            type: "get",
                            url: "/" + resource + "/select2",
                            success: function (data) {{
                                var temp_arr = []
                                    for(var j in data){{
                                        temp_arr[j] = {{
                                            id: data[j]['$id']
                                        }}
                                        if(resource == 'province'){{
                                            temp_arr[j]['text'] = data[j].type + " " + data[j].name
                                        }} else {{
                                            temp_arr[j]['text'] = data[j].name
                                        }}
                                    }}
                                    $(select2_elements[i]).select2({{
                                        width: '100%',
                                        data: temp_arr
                                    }});
                                    $(select2_elements[i + h]).select2({{
                                        width: '100%',
                                        data: temp_arr
                                    }});
                                }},
                                error: function (request, status, error) {{
                                    console.log(request);
                                    console.log(error);
                                    alert(request.responseText);
                                }}
                        }});
                    }}
                    
                    if(select2_elements.length){{
                        var h = select2_elements.length / 2;
                        for(var i = 0; i < h;i++){{
                            var element_id = select2_elements[i].getAttribute('id');
                            if(element_id.startsWith('load_now')){{
                                var resource = element_id.split('-')[1]
                                if(resource == 'province'){{
                                    if(!{0}){{
                                        select2_ajax(i, h, resource);
                                    }}
                                }} else {{
                                    select2_ajax(i, h, resource);
                                }}
                            }}
                        }}
                    }}
                        
            """.format(has_province_id)

        def convert_column_display(column_type):
            render_result = ""
            render_tmpl = """"render": function (data, type, row) {{
                                        return "{0}" + {2} + "{1}"
                                    }}"""
            if column_type == g.c.LINK_DISP:
                render_result = render_tmpl.format("<a>", "</a>", "(data ? data : '')")
            if column_type == g.c.BOLD_DISP:
                render_result = render_tmpl.format("<b>", "</b>", "(data ? data : '')")
            if column_type == g.c.FarmerType:
                render_result = render_tmpl.format(
                    "", "",
                    "(data == 1 ? \"" + _('member') + "\" : \"" + _('reviewer') + "\")")
            if column_type == g.c.GenderType:
                render_result = render_tmpl.format(
                    "", "",
                    "(data == 1 ? \"" + _('male') + "\" : \"" + _('female') + "\")")
            if column_type == g.c.CertificateStatusType:
                render_result = render_tmpl.format(
                    "", "",
                    "(data==1?\"" + """<div class=\\"form-group has-success\\"><label class=\\"control-label\\"><i class=\\"fa fa-check-circle-o\\"></i> """ + _(
                        'approved') + "</label></div>" +
                    "\":data==2?\"" + """<div class=\\"form-group has-error\\"><label class=\\"control-label\\"><i class=\\"fa fa-times-circle-o\\"></i> """ + _(
                        'rejected') + "</label></div>" +
                    "\":data==3?\"" + """<div class=\\"form-group has-warning\\"><label class=\\"control-label\\"><i class=\\"fa fa-warning\\"></i> """ + _(
                        'in_conversion') + "</label></div>" +
                    "\":\"" + """<div class=\\"form-group has-success\\"><label class=\\"control-label\\"><i class=\\"fa fa-check-circle-o\\"></i>""" + _(
                        'approved_no_cert') + "</label></div>\")")
            if column_type == g.c.CertificateReVerifyStatusType:
                render_result = render_tmpl.format(
                    "", "",
                    "(data==1?\"" + """<div class=\\"form-group has-success\\"><label class=\\"control-label\\"><i class=\\"fa fa-check-circle-o\\"></i> """ + _(
                        'not_check') + "</label></div>" +
                    "\":data==2?\"" + """<div class=\\"form-group has-success\\"><label class=\\"control-label\\"><i class=\\"fa fa-check-circle-o\\"></i> """ + _(
                        'valid') + "</label></div>" +
                    "\":data==3?\"" + """<div class=\\"form-group has-error\\"><label class=\\"control-label\\"><i class=\\"fa fa-times-circle-o\\"></i> """ + _(
                        'decline') + "</label></div>" +
                    "\":data==4?\"" + """<div class=\\"form-group has-warning\\"><label class=\\"control-label\\"><i class=\\"fa fa-warning\\"></i> """ + _(
                        'warning') + "</label></div>" +
                    "\":\"" + """<div class=\\"form-group has-error\\"><label class=\\"control-label\\"><i class=\\"fa fa-times-circle-o\\"></i> """ + _(
                        'punish') + "</label></div>" + "\")")
            return render_result

        def get_ajax_config(is_table_of_current_content=True):
            url = ajax_endpoint
            ajax_config = """
                "serverSide": true,
                "ajax": function(data, callback, settings) {
                    var sort_column_name = data.columns[data.order[0].column].data;
                    var direction = data.order[0].dir == 'asc' ? true : false
                    var where_params = {}
            """
            if is_table_of_current_content:
                if ajax_endpoint != 'user':
                    ajax_config += """
                        where_params = {"_deleted_at":null}
                    """
            else:
                url += "/deleted"
            ajax_config += """
                    var sort_params = {{}}
                    sort_params[sort_column_name] = direction; 
                    if (data.search.value) {{
                        for (idx in data.columns) {{
                            if (data.columns[idx].searchable && 
                                data.columns[idx].data != "_deleted_at" &&
                                data.columns[idx].data != "group_area" &&
                                data.columns[idx].data != "member_count" &&
                                data.columns[idx].data != "certificate_start_date" &&
                                data.columns[idx].data != "certificate_expiry_date") {{
                                where_params[data.columns[idx].data] = {{}};
                                where_params[data.columns[idx].data]["$contains"]=data.search.value;
                            }}
                        }}
                    }};
                    $.get('/{0}', {{
                        per_page: data.length,
                        page: data.start/data.length + 1,
                        where: JSON.stringify(where_params),
                        sort: JSON.stringify(sort_params)
                        }}, 
                        function(res, status, req) {{
                            callback({{
                                recordsTotal: req.getResponseHeader('X-Total-Count'),
                                recordsFiltered: req.getResponseHeader('X-Total-Count'),
                                data: res
                            }});
                        }});
                }},
            """.format(url)
            return ajax_config

        if current_app.config['AJAX_CALL_ENABLED']:
            mapping = ""
            for column in column_names:
                if column[0] == 'action':
                    render_func = """"render": function (data, type, row) {{
                        data_attr = ''
                        row_attr = Object.keys(row)
                        for (idx in row_attr) {{
                            if (row_attr[idx].startsWith('_') == false) {{
                                value = row[row_attr[idx]]
                                data_attr += 'data-' + row_attr[idx].replace(/[$]/g, '') + '=\"' + value + '\" '
                            }}
                        }}
                        if('{5}' == 'user'){{
                            if(row['roles'].length > 0){{
                                for(var i in row['roles']){{
                                    var user_role_id = row['roles'][i]["$ref"].split('/')[2];
                                    for(var r in roles){{
                                        if(user_role_id == roles[r]['$id']){{
                                            data_attr += 'data-multi-select-' + roles[r]['name'] +
                                                            '=\"' + roles[r]['name'] + '\"';
                                            break;
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        return "<button type=\\"button\\" class=\\"btn {0} {1} {2}\\"" +
                        "data-toggle=\\"modal\\" data-target=\\"#{3}\\"" +
                        data_attr +
                        ">" +
                        "<i class=\\"fa fa-{4}\\"></i></button>" + 
                        " " +
                    """.format(g.c.BTNEDIT_ID, 'btn-xs', 'btn-info',
                               g.c.MODAL_EDIT_ID, 'edit', ajax_endpoint)

                    if has_button_view:
                        render_func += """
                            "<button type=\\"button\\" class=\\"btn {1} {0} {2}\\"" +
                            "data-toggle=\\"modal\\" data-target=\\"#{4}\\"" +
                            data_attr +
                            ">" +
                            "<i class=\\"fa fa-{3}\\"></i></button>" + 
                            " " +
                        """.format('btn-xs', g.c.BTNVIEW_ID, 'btn-warning', 'search',
                                     g.c.MODAL_DETAIL_ID)

                    render_func += """
                            "<button type=\\"button\\" class=\\"btn {0} {1} {2}\\"" +
                            "data-toggle=\\"modal\\" data-target=\\"#{3}\\"" +
                            data_attr +
                            ">" +
                            "<i class=\\"fa fa-{4}\\"></i></button>"
                        }}""".format('btn-xs', g.c.BTNDEL_ID,
                                     'btn-danger', g.c.MODAL_DEL_ID, 'trash')
                    mapping += """
                        {{"orderable": {1}, "searchable": {1},
                            "width": "10%", 
                         {0}}},""" \
                        .format(render_func, str(column[1]).lower())
                else:
                    render_func = convert_column_display(column[2])
                    mapping += """
                        {{"data": "{1}", "orderable": {2}, "searchable": {2},
                         {0}}},""" \
                        .format(render_func, column[0], str(column[1]).lower())

            server_script = """
                    {0}
                    "columns": [{1}
                    ],""".format(get_ajax_config(True), mapping)
        else:
            server_script = """
            "serverSide": false,
            """
        datatable_config = """
            "language": {{
                "url": "/static/{0}.json"
            }},
            buttons: [
                {{
                    extend: 'excelHtml5',
                    text: '<i class="fa fa-file-excel-o"></i>',
                    titleAttr: 'Excel',
                    exportOptions: {{
                        columns: [{1}]
                    }}
                }},
                {{
                    extend: 'pdfHtml5',
                    text: '<i class="fa fa-file-pdf-o"></i>',
                    titleAttr: 'PDF',
                    exportOptions: {{
                        columns: [{1}]
                    }}
                }},
                {{
                    extend: 'print',
                    text: '<i class="fa fa-print"></i>',
                    titleAttr: 'Print',
                    exportOptions: {{
                        columns: [{1}]
                    }}
                }}
            ],
            "processing": true,
            "paging": true,
            "pagingType": "full_numbers",
            "lengthChange": true,
            "searching": true,
            "ordering": true,
            "info": true,
            "autoWidth": true,
        """.format(g.language, export_columns)

        column_of_deleted_data = ""
        init_complete_config = """
            table.buttons().container().appendTo('#pgs_data_filter');
            $('.dt-buttons').css("margin-left", "5px")
        """

        if ajax_endpoint in g.c.PAGE_HAVE_SOFT_DELETE:
            for column in column_names:
                if column[0] != 'action':
                    render_func = convert_column_display(column[2])
                    column_of_deleted_data += """
                        {{"data": "{1}", "orderable": {2}, "searchable": {2}, "title": "{3}", {0} }},
                    """.format(render_func, column[0], str(column[1]).lower(), str(column[3]))
            column_of_deleted_data += """
                {{ "data": "_deleted_at", "title": "{0}", "searchable": "true" }},
                {{ "data": "_modify_info", "title": "{1}", "searchable": "true" }},    
            """.format(str(_('Deleted at')), str(_('Reason')))

            init_complete_config += """
                $('#pgs_data_filter label').append('<select class="form-control input-sm" id="{0}"' +
                    'style="display: inline-block; width: auto;">' +
                        '<option value="none_delete">{2}</option>' +
                        '<option value="deleted">{1}</option>' +
                    '</select>'
                )
            """.format('search_type', _('Deleted'), _('Current'))

        grop_agroup_script = ""
        if ajax_endpoint == "associate_group":
            grop_agroup_script = load_agroup_script()
        elif ajax_endpoint == "group":
            grop_agroup_script = load_group_script()

        script = """
        {0}
        <!-- page script -->
        <script>
            $(function () {{
            
                var roles = [];
                if('{14}' == 'user'){{
                    $.ajax({{
                        type: "get",
                        url: '/role',
                        success: function (data, text) {{
                            roles = data;
                        }},
                        error: function (request, status, error) {{
                            console.log(request);
                            console.log(error);
                        }}
                    }});
                }}
            
                function create_dataTable(){{
                    var table = $('#pgs_data').DataTable({{
                        {17}
                        {1}
                        "drawCallback": function( settings ) {{
                            $('.{2}').on('click', function (event) {{
                                
                                var data = $(this).data()
                                var modal = $('#{3}')
                                
                                function call_ajax(url, resource, id_resource, element_id, default_value){{
                                    $.ajax({{
                                        type: "get",
                                        url: url,
                                        data: 'where={{"' + resource + '": ' +
                                            '{{"$ref": "/' + resource + '/' + id_resource + '"}} }}',
                                        success: function (data, text) {{
                                            var select2_data = [];
                                            for (var i = 0; i < data.length; i++) {{
                                                select2_data[i] = {{
                                                    id: data[i]['$id'],
                                                    text: data[i].type + " " + data[i].name
                                                }}
                                            }}
                                            modal.find('#'+element_id).select2({{ width: '100%', data: select2_data}})
                                                .val(default_value).trigger('change.select2');
                                        }},
                                        error: function (request, status, error) {{
                                            console.log(request);
                                            console.log(error);
                                            alert(request.responseText);
                                        }}
                                    }});
                                }}
                                
                                var s2 = $('.{10}')
                                var multi_select_data = []
                                for (var key in data) {{
                                    var target = modal.find('#' + key)
                                    var get_resource = key.split('_id');
                                    if(!target.length && get_resource.length > 1){{
                                        var load_resource = get_resource[0];
                                        if (load_resource.startsWith('owner')){{
                                            load_resource = get_resource[0].split('_')[1];
                                        }}
                                        target = modal.find('#load_now-'+ load_resource);
                                    }}
                                    value = ''
                                    if (data[key]!='None'){{value = data[key]}}
                                    if (target.is('select')){{
                                        target.val(data[key]).trigger('change.select2')
                                    }} else {{
                                        modal.find('#' + key).val(value)
                                    }}
                                    if (key.startsWith('multiSelect')) {{
                                        multi_select_data.push(data[key])
                                    }}
                                }}
                                if(s2.length > 0 && multi_select_data.length > 0){{
                                    s2.val(multi_select_data).trigger("change")
                                }}
    
                                var op = modal.find('#{12}')
                                if(op.length > 0 ){{
                                    op.parent().removeClass('hidden')
                                    modal.find('#password').prop('required',false)
                                    modal.find('#password').parent().removeClass('required')
                                    modal.find('#confirm').prop('required',false)
                                    modal.find('#confirm').parent().removeClass('required')
                                }}
                                
                                if(data['province_id'] && data['district_id']){{
                                    modal.find('#district_id').empty();
                                    call_ajax('/district', 'province', data['province_id'],
                                        'district_id', data['district_id']);
                                }}
                                
                                if(data['district_id'] && data['ward_id']){{
                                    modal.find('#ward_id').empty();
                                    call_ajax('/ward', 'district', data['district_id'],
                                        'ward_id', data['ward_id']);
                                }}
                            }})
                            $('.{5}').on('click', function (event) {{
                                var modal_add = $('#{11}')
                                modal_add.find('#id').val('')
                                var op = modal_add.find('#{12}')
                                if(op.length > 0 ){{
                                    op.parent().addClass('hidden')
                                    modal_add.find('#password').prop('required',true)
                                    modal_add.find('#password').parent().addClass('required')
                                    modal_add.find('#confirm').prop('required',true)
                                    modal_add.find('#confirm').parent().addClass('required')
                                }}
                            }})
                            $('.{6}').on('click', function (event) {{
                                var data = $(this).data()
                                var modal_del = $('#{7}')
                                modal_del.find('#id').val(data['id'])
                            }})
                            $('#{9}').removeClass('btn-primary')
                            .addClass('btn-warning')
                            
                            
                            {19}
                            
                        }},
                        "initComplete": function (settings, json) {{
                            $('.{5}').appendTo('#pgs_data_filter');
                            $('.{5}').css("margin-left", "5px");
                            {16}
                            $('#{13}').change(function () {{
                                var search_type = $('#{13}').val();
                                if(search_type == "deleted"){{
                                    table.destroy();
                                    $('#pgs_data').empty();
                                    var columns = [{15}];      
                                    table = $('#pgs_data').DataTable({{
                                        {18}
                                        {1}
                                        columns : columns,
                                        "initComplete": function (settings, json) {{
                                            {16}
                                            var search_type_element = $("#{13}");
                                            search_type_element.val('deleted');
                                            search_type_element.change(function () {{
                                                var search_type = search_type_element.val();
                                                if(search_type == "none_delete"){{
                                                    table.destroy();
                                                    $('#pgs_data').empty();
                                                    table = create_dataTable();
                                                }}
                                            }});
                                        }}
                                    }}) 
                                }}
                            }});
                        }},
                    }})
                    return table;
                }}
                var table = create_dataTable();
                    
                if('{14}' == 'certificate/groups'){{
                    var modal_edit = $('#{3}');
                    modal_edit.find('#load_now-farmer').parent().remove();
                    var modal_add = $('#{11}');
                    modal_add.find('#load_now-farmer').parent().remove();
                }} else if('{14}' == 'certificate/farmers'){{
                var modal_edit = $('#{3}');
                    modal_edit.find('#load_now-group').parent().remove();
                    var modal_add = $('#{11}');
                    modal_add.find('#load_now-group').parent().remove();
                }}
                
                {4}
                $('.{8}').removeClass('btn-default')
                    .addClass('btn-primary pull-right')
                    .before("<hr />" )
                $('.{8}').parent()
                    .append('<button type="button" class="pgs_dismiss_modal btn btn-default"'+
                    'data-dismiss="modal">Cancel</button>');
                    
        """.format(datatables_script, datatable_config, g.c.BTNEDIT_ID,
                   g.c.MODAL_EDIT_ID, select2_script, g.c.BTNADD_ID,
                   g.c.BTNDEL_ID, g.c.MODAL_DEL_ID, g.c.SUBMIT_DEFAULT_CLASS,
                   g.c.DEL_SUBMIT_ID, g.c.MULTI_SELECT_DEFAULT_CLASS,
                   g.c.MODAL_ADD_ID, 'old_pass', 'search_type',
                   ajax_endpoint, column_of_deleted_data, init_complete_config,
                   server_script, get_ajax_config(False), grop_agroup_script)

        if len(crud_endpoint) == 3:
            script += """
                var table = table;
                function form_submit(endpoint, form_index, method){{
                    $('form:eq(' + form_index + ')').submit(function(e){{
                        // form add object
                        $.ajax({{
                            type: method,
                            url: endpoint,
                            data: $('form:eq(' + form_index + ')').serialize(),
                            success: function (data) {{
                                if(data.is_success){{
                                    toastr.success(data.message);
                                    table.ajax.reload();
                                }} else {{
                                    toastr.error(data.message);
                                }}
                            }}
                        }});
                        e.preventDefault();
                        $('.pgs_dismiss_modal').click();
                    }});
                }};
                
                // add form
                form_submit("{0}", 1, "POST");
                
                // edit form
                form_submit("{1}", 2, "PUT");
                
                // delete form
                form_submit("{2}", 3, "DELETE");
            """.format(lurl_for(crud_endpoint[0]), lurl_for(crud_endpoint[1]), lurl_for(crud_endpoint[2]))

        script += """
            });
        </script>
            """
        return Markup(script)
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


def load_group_script():
    certificate_status_type = {}
    for key in g.c.CertificateStatusType:
        certificate_status_type[key.value] = _(key.name)

    certificate_re_verify_status_type = {}
    for key in g.c.CertificateReVerifyStatusType:
        certificate_re_verify_status_type[key.value] = _(key.name)

    gender_type = {}
    for key in g.c.GenderType:
        gender_type[key.value] = _(key.name)

    farmer_type = {}
    for key in g.c.FarmerType:
        farmer_type[key.value] = _(key.name)

    group_script = """
            var elements_select2 = $('select');

            function catch_select2_select_event(source_element, url, resource, des1_element, des2_element) {{
                $(source_element).on("select2:select", function (e) {{
                    $(des1_element).empty();
                    if (des2_element) {{
                        $(des2_element).empty();
                    }}
                    var value = e.target.value;
                    $.ajax({{
                        type: "get",
                        url: url,
                        data: 'where={{"' + resource + '": {{"$ref": "/' + resource + '/' + value + '"}} }}',
                        success: function (data, text) {{
                            var select2_data = [];
                            for (var i = 0; i < data.length; i++) {{
                                select2_data[i] = {{
                                    id: data[i]['$id'],
                                    text: data[i].type + " " + data[i].name
                                }}
                            }}
                            $(des1_element).select2({{data: select2_data}});
                        }},
                        error: function (request, status, error) {{
                            console.log(request);
                            console.log(error);
                            alert(request.responseText);
                        }}
                    }});
                }});
            }}

            catch_select2_select_event(elements_select2[0], '/district', 'province', 
                elements_select2[1], elements_select2[2]);

            catch_select2_select_event(elements_select2[4], '/district', 'province', 
                elements_select2[5], elements_select2[6]);

            catch_select2_select_event(elements_select2[1], '/ward', 'district', 
                elements_select2[2], NaN);
            
            catch_select2_select_event(elements_select2[5], '/ward', 'district',
                elements_select2[6], NaN);
                
            var certificate_status_type = {5};
            var certificate_re_verify_status_type = {6};
            
            var gender_type = {7};
            var farmer_type = {8};
            
            $('.{2}').on('click', function () {{
                var owner_group_id = $(this).data()['owner_group_id'];
                $.ajax({{
                    type: "get",
                    url: '/certificate',
                    data: 'where={{"owner_group_id": "' + owner_group_id + '"}}',
                    success: function (data, text) {{
                        $('#{0}').find("tr:gt(0)").remove();
                        if (data.length) {{
                            var table_body = $('#{0} tbody');
                            for (var i in data) {{
                                var new_row = '<tr>' +
                                    '<th scope="row">' + (parseInt(i) + 1) + '</th>' +
                                    '<td><b>' + data[i]['certificate_code'] + '</b></td>' +
                                    '<td>' + data[i]['gov_certificate_id'] + '</td>' +
                                    '<td>' + certificate_status_type[data[i]['status']] + '</td>' +
                                    '<td>' + certificate_re_verify_status_type[data[i]['re_verify_status']] + '</td>' +
                                    '<td>' + data[i]['certificate_start_date'] + '</td>' +
                                    '<td>' + data[i]['certificate_expiry_date'] + '</td>' +
                                    '<td>' + data[i]['_modify_info'] + '</td>' +
                                    '</tr>';
                                table_body.append(new_row);
                            }}
                        }}
                    }},
                    error: function (request, status, error) {{
                        console.log(request);
                        console.log(error);
                        alert(request.responseText);
                    }}
                }});
            }})
            
            function get_info_of_group(url, data, des_id_element) {{
                $.ajax({{
                    url: url,
                    data: data,
                    success: function (data, status, req) {{
                        var count;
                        if(url == '/group/group_summary'){{
                            data = JSON.parse(data);
                            count = data['total_of_farmer'] + " (" + data['total_of_male'] + 
                                    " / " + data['total_of_female'] + ")";
                        }} else {{
                            count = data.length;
                            var total_area_approved = 0;
                            var total_area = 0;
                            for(var i in data){{
                                total_area += data[i]['group_area'];
                                if(data[i]['status'] == {3} || 
                                   data[i]['status'] == {4} ){{
                                   total_area_approved += data[i]['group_area'];
                                }}
                            }}
                            $('#label_sum2').html(total_area_approved + ' / ' + total_area);
                        }}
                        $('#'+des_id_element).html(count);
                    }},
                    error: function (request, status, error) {{
                        console.log(request);
                        console.log(error);
                    }}
                }})
            }}
            $('.{1}').on('click', function (event) {{
                var group_id = $(this).data()['id'];
                var d1 = 'id="' + group_id + '"';
                get_info_of_group('/group/group_summary', d1, 'label_sum1');
                var d2 = 'where={{"owner_group_id": "' + group_id + '"}}';
                get_info_of_group('/certificate/total', d2, 'label_sum0');
                
                $.ajax({{
                    method: 'GET',
                    url: '/farmer/deleted',
                    data: 'where={{"group_id": "' + group_id + '"}}',
                    success: function (data, status, req) {{
                        $('#{9}').find('tr:gt(0)').remove()
                        if(data.length){{
                            $('#{10}').addClass('hidden');
                            $('#{9} div').removeClass('hidden');
                            var table_body = $('#{9} table tbody');
                            for (var i in data) {{
                                var new_row = '<tr>' +
                                    '<th scope="row">' + (parseInt(i) + 1) + '</th>' +
                                    '<td><b>' + data[i]['farmer_code'] + '</b></td>' +
                                    '<td>' + data[i]['name'] + '</td>' +
                                    '<td>' + gender_type[data[i]['gender']] + '</td>' +
                                    '<td>' + farmer_type[data[i]['type']] + '</td>' +
                                    '<td>' + data[i]['_deleted_at'] + '</td>' +
                                    '<td>' + data[i]['_modify_info'] + '</td>' +
                                    '</tr>';
                                table_body.append(new_row);
                            }}
                        }} else {{
                            $('#{10}').removeClass('hidden');
                            $('#{9} div').addClass('hidden');
                        }}
                    }},
                    error: function (request, status, error) {{
                        console.log(request);
                        console.log(error);
                        alert(request.responseText);
                    }}
                }})
            }});
    """.format(g.c.MODAL_HISTORY_ID, g.c.BTNVIEW_ID, 'view_gr_history',
               g.c.CertificateStatusType['approved'].value,
               g.c.CertificateStatusType['approved_no_cert'].value,
               json.dumps(certificate_status_type), json.dumps(certificate_re_verify_status_type),
               json.dumps(gender_type), json.dumps(farmer_type),
               'tab_history', 'no_data')
    return group_script


def load_agroup_script():
    agroup_script = """
                $('.{0}').on('click', function (event) {{
                    var agroup_id = $(this).data()['id'];
                    $.ajax({{
                        method: 'GET',
                        url: '/associate_group/agroup_summary',
                        data: 'id="' + agroup_id + '"',
                        success: function (data, status, req) {{
                            data = JSON.parse(data)
                            $('#label_sum0').html(data['total_of_cert']);
                            $('#label_sum1').html(data['total_of_gr']);
                            $('#label_sum2').html(data['total_of_farmer'] + ' (' + data['total_of_male'] + ' / ' + 
                                    data['total_of_female'] + ')');
                            $('#label_sum3').html(data['total_of_approved_area'] + ' / ' + data['total_of_area']);
                        }},
                        error: function (request, status, error) {{
                            console.log(request);
                            console.log(error);
                            alert(request.responseText);
                        }}
                    }})
                    
                    $.ajax({{
                        method: 'GET',
                        url: '/group/deleted',
                        data: 'where={{"associate_group_id": "' + agroup_id + '"}}',
                        success: function (data, status, req) {{
                            $('#{1}').find('tr:gt(0)').remove()
                            if(data.length){{
                                $('#{2}').addClass('hidden');
                                $('#{1} div').removeClass('hidden');
                                var table_body = $('#{1} table tbody');
                                for (var i in data) {{
                                    var new_row = '<tr>' +
                                        '<th scope="row">' + (parseInt(i) + 1) + '</th>' +
                                        '<td><b>' + data[i]['group_code'] + '</b></td>' +
                                        '<td>' + data[i]['name'] + '</td>' +
                                        '<td>' + data[i]['village'] + '</td>' +
                                        '<td>' + data[i]['ward']['name'] + '</td>' +
                                        '<td>' + data[i]['district']['name'] + '</td>' +
                                        '<td>' + data[i]['province']['name'] + '</td>' +
                                        '<td>' + data[i]['_deleted_at'] + '</td>' +
                                        '<td>' + data[i]['_modify_info'] + '</td>' +
                                        '</tr>';
                                    table_body.append(new_row);
                                }}
                            }} else {{
                                $('#{1} div').addClass('hidden');
                                $('#{2}').removeClass('hidden');
                            }}
                        }},
                        error: function (request, status, error) {{
                            console.log(request);
                            console.log(error);
                            alert(request.responseText);
                        }}
                    }})
                        
                }});
    
    """.format(g.c.BTNVIEW_ID, 'tab_history', 'no_data')
    return agroup_script


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
