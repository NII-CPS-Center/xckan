import csv
from datetime import datetime
import filelock
import json
from logging import getLogger
import os
import requests
import simplejson

from django.contrib import messages
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import \
    require_http_methods, require_GET, require_POST
from django.views.generic import ListView, TemplateView, UpdateView
from django.shortcuts import redirect
from pysolr import SolrError

from .api import api
from xckan.siteconf import site_config

from .models import Site

logger = getLogger(__name__)
mimetype = 'application/json;charset=utf-8'


class SiteIndexView(TemplateView):
    template_name = 'sites/index.html'


class SiteSettingIndexView(ListView):
    model = Site
    context_object_name = 'sites'
    paginate_by = 10

    fields = [
        'title', 'enable',
        'executed_at', 'result', 'update_time',
        'full_executed_at', 'full_result', 'full_update_time',
    ]

    def __init__(self, **kwargs):
        """
        Custom initializer

        Initalize list condition `self.conds`.
        """
        self.conds = None
        return super().__init__(**kwargs)

    def get_queryset(self):
        """
        Set query conditions.
        """
        if self.conds is None:
            # Set conditions from cookie
            self.conds = dict(self.request.session.items())

        get_conds = self.request.GET
        for key in ('key', 'sort_by', 'rows', 'page'):
            if key in get_conds:
                if self.conds is None:
                    self.conds = {}
                elif key not in self.conds\
                        or self.conds[key] != get_conds.get(key):
                    self.conds['page'] = 1

                self.conds[key] = get_conds.get(key)

        # Building query
        sites = Site.objects.all()

        # Filter by title and dataset_url
        q = self.conds.get('key', None)
        if q is not None and len(q) > 0:
            sites = sites.filter(
                Q(title__contains=q)
                | Q(dataset_url__contains=q)
            ).distinct()

        # 並び替え
        sort_key = self.conds.get('sort_by', None)
        if sort_key is None:
            sort_param = ['-enable', 'result', 'full_result', 'id']
        else:
            sort_param = [sort_key]

        sites = sites.order_by(*sort_param)

        return sites

    def get_context_data(self, **kwargs):
        if 'rows' in self.conds:
            self.paginate_by = int(self.conds['rows'])

        if 'page' in self.conds:
            self.kwargs = {'page': self.conds['page']}

        context = super().get_context_data(**kwargs)
        context['fields'] = self.fields
        context['yesno_fields'] = ['enable', ]
        if len(self.object_list) > 0:
            context['top'] = self.object_list[0]
        else:
            context['top'] = None

        context.update({
            'key': self.conds.get('key', ''),
            'rows': self.conds.get('rows', '10'),
            'sort_by': self.conds.get('sort_by', ''),
        })

        # Save conditions to the session cookie
        for k, v in self.conds.items():
            self.request.session[k] = v

        return context


class SiteSettingDetailView(UpdateView):
    model = Site
    context_object_name = 'site'
    fields = ['memo']


def get_args(request):
    if request.method == "GET":
        args = request.GET
    elif request.method == "POST":
        args = request.POST
    return args


@csrf_exempt
@require_http_methods(["GET", "POST"])
def package_list(request):
    args = get_args(request)
    try:
        result = api.package_list(**args)
        success = True
    except Exception as e:
        result = str(e)
        success = False

    obj = {
        "help": request.build_absolute_uri(),
        "success": success,
        "result": result
    }
    r = JsonResponse(obj)
    if mimetype:
        r.mimetype = mimetype
    return r


@csrf_exempt
@require_http_methods(["GET", "POST"])
def package_show(request):
    args = get_args(request)
    try:
        result = api.package_show(**args)
        success = True
    except Exception as e:
        result = str(e)
        success = False

    obj = {
        "help": request.build_absolute_uri(),
        "success": success,
        "result": result
    }
    r = JsonResponse(
        obj,
        json_dumps_params={"ensure_ascii": False},
        safe=False)

    if mimetype:
        r.mimetype = mimetype
    return r


@csrf_exempt
@require_http_methods(["GET", "POST"])
def package_search(request):
    args = get_args(request)

    # Query log
    now = datetime.now()
    log_data = [
        now.isoformat(timespec='milliseconds'),
        args.get('q', '*:*'),
        args.get('fq', '*:*'),
    ]

    os.makedirs(site_config.QUERYLOGDIR, mode=0o755, exist_ok=True)
    log_file = os.path.join(site_config.QUERYLOGDIR,
                            "{}.log".format(now.strftime('%Y-%m-%d')))
    lock_name = log_file + '.lck'
    with filelock.FileLock(lock_name):
        with open(log_file, 'a+', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(log_data)

    status_code = 200
    try:
        result = api.package_search(**args)
        success = True
    except SolrError as e:
        if "org.apache.solr.search.SyntaxError" in str(e):
            status_code = 400
            result = ("Cannot parse the request parameter.")
        else:
            status_code = 503
            result = (
                "The backend Solr server is not responding. "
                "Please retry later."
            )

        success = False
    except Exception as e:
        status_code = 400
        result = str(e)
        success = False

    obj = {
        "help": request.build_absolute_uri(),
        "success": success,
        "result": result
    }

    r = JsonResponse(obj, status=status_code)
    if mimetype:
        r.mimetype = mimetype
    return r


@csrf_exempt
@require_http_methods(["GET", "POST"])
def hot_tag(request):
    results = {
        "医療": 16421,
        "統計": 13601,
        "環境": 6213,
        "健康": 1636,
        "情報公開": 236
    }
    r = JsonResponse(results)
    r.mimetype = mimetype
    return r


@csrf_exempt
@require_http_methods(["GET", "POST"])
def stat(request):
    args = get_args(request)
    try:
        result = api.site_statistics(**args)
        success = True
    except Exception as e:
        result = str(e)
        success = False

    obj = {
        "help": request.build_absolute_uri(),
        "success": success,
        "result": result
    }

    r = JsonResponse(obj)
    if mimetype:
        r.mimetype = mimetype
    return r


def validate_dataset(url):
    output = {'success': False, 'message': ''}
    with requests.Session() as session:
        try:
            resp = session.get(
                url, timeout=5,
                verify=not site_config.ACCEPT_SELF_SIGNED)
            resp.raise_for_status()
            output['success'] = True
        except Exception as e:
            output['success'] = False
            output['message'] = str(e)
    return output


def validate_json_response(url):
    output = {'success': False, 'result': None, 'message': ''}
    with requests.Session() as session:
        try:
            resp = session.get(
                url, timeout=5,
                verify=not site_config.ACCEPT_SELF_SIGNED)
            resp.raise_for_status()
            data = resp.json()
            output['success'] = data.get('success', False)
            output['result'] = data.get('result', None)
        except simplejson.errors.JSONDecodeError:
            output['success'] = False
            output['message'] = 'It is not JSON'
        except Exception as e:
            output['success'] = False
            output['message'] = str(e)
    return output


@require_GET
def site_validator(request, *args, **kwargs):
    """
    Validate site configuration
    """
    result = {'dataset_url': {}, 'ckanapi_url': {}, 'fq': {}}
    if not request.user or not request.user.is_authenticated or \
            not request.user.has_perm('sites.add_site'):
        return JsonResponse(result, status=401)

    site = Site.objects.get(pk=kwargs['pk'])
    if not site:
        return JsonResponse(result, status=404)

    site.enable = True

    # Check the dataset url is reachable.
    result['dataset_url'] = validate_dataset(site.dataset_url)

    # Check the api url.
    result['package_list'] = validate_json_response(
        site.ckanapi_url + 'package_list?limit=1')
    if result['package_list']['success'] is True:
        sample_id = result['package_list']['result'][0]
        result['ckanapi_url'] = validate_json_response(
            site.ckanapi_url + 'package_show?id={id}'.format(
                id=sample_id))
    else:
        result['ckanapi_url'] = {
            'success': False, 'result': None,
            'message': 'Failed to execute package_list API'}

    if site.proxy_url:
        result['proxy_url'] = validate_json_response(
            site.proxy_url + 'package_search?q=*:*&rows=0')
    else:
        result['proxy_url'] = {'success': True}

    if result['dataset_url']['success'] is False:
        site.enable = False

    if result['ckanapi_url']['success'] is False:
        site.enable = False

    # Check fq query is available or not.
    now_ymd = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    check_url = site.ckanapi_url + 'package_search?q=*:*&fq=' + \
        '(metadata_modified:["{}" TO *] OR '.format(now_ymd) + \
        'metadata_created:["{}" TO *])&rows=0'.format(now_ymd)
    fq_result = validate_json_response(check_url)
    if fq_result['success'] is False:
        if site.is_fq_available:
            site.is_fq_available = False
            result['fq'] = {
                'success': False,
                'message': "差分更新を「不可」に変更しました",
            }
        else:
            result['fq'] = {
                'success': True,
                'message': "差分更新は不可です",
            }
    else:
        if site.is_fq_available:
            result['fq'] = {
                'success': True,
                'message': "差分更新可能です",
            }
        else:
            site.is_fq_available = True
            result['fq'] = {
                'success': False,
                'message': "差分更新を「可」に変更しました",
            }

    if site.enable:
        result['enable'] = {
            'success': True,
            'message': '次の周期から更新を開始します'
        }
    else:
        result['enable'] = {
            'success': False,
            'message': '更新を停止します'
        }

    if site.enable:
        site.update_time = site.next_update_time()

    site.save()

    return JsonResponse(result)


@require_POST
def site_import(request):
    """
    Upload the JSON file and import the site list.
    """
    if not request.user or not request.user.is_authenticated or \
            not request.user.has_perm('sites.add_site'):
        return JsonResponse(
            {'success': False, 'message': '権限がありません'},
            json_dumps_params={'ensure_ascii': False},
            status=401)

    uploaded_file = request.FILES.get('files', None)
    if uploaded_file is None:
        return JsonResponse(
            {'success': False,
             'message': 'JSONファイルがアップロードされていません'},
            json_dumps_params={'ensure_ascii': False}, status=400)

    deserialized = json.loads(str(uploaded_file.read(), 'utf-8'))
    new_sites = {}

    for data in deserialized:
        for field in ['id', 'result', 'executed_at',
                      'full_result', 'full_executed_at']:
            if field in data:
                del data[field]

        try:
            # If there is a site with matching dataset_url,
            # update the information for that site.
            site = Site.objects.get(dataset_url=data['dataset_url'])
            for attr, value in data.items():
                setattr(site, attr, value)

            site.save()
        except Site.DoesNotExist:
            # Otherwise, create a new site.
            data['enable'] = False
            if data['dataset_url'] in new_sites:
                messages.add_message(
                    request, messages.WARNING,
                    '{title} は dataset_url が重複するため無視されました。'.format(
                        title=data['title'])
                )
            else:
                new_sites[data['dataset_url']] = Site(**data)

    if len(new_sites) > 0:
        Site.objects.bulk_create(new_sites.values())

    return redirect('index')


@require_GET
def site_export(request):
    """
    Export the site list as a JSON file.
    """
    if not request.user or not request.user.is_authenticated or \
            not request.user.has_perm('sites.add_site'):
        return JsonResponse(
            {'success': False, 'message': '権限がありません'}, status=401)

    sites = Site.objects.all()
    site_list = list(map(model_to_dict, sites))
    for site in site_list:
        for field in ['id', 'result', 'executed_at',
                      'full_result', 'full_executed_at']:
            del site[field]

    response = JsonResponse(
        list(site_list),
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 2},
        content_type='application/json; charset=utf-8')

    filename = 'xckan_sitelist_{}.json'.format(
        datetime.now().strftime('%Y%m%d-%H%M%S'))
    response['Content-Disposition'] = 'attachment; filename={}'.format(
        filename)
    return response
