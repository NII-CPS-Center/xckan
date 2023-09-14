# encoding: utf-8

# How to perform the test
# Prerequisites: solr is up
#
# cd ckan-xsearch/django-backend
# python manage.py test

import io
import json
from unittest import mock
from django.contrib.auth.models import User
from django.utils.http import urlencode
from django.test import TestCase, Client
from django.urls import reverse

from sites.models import Site


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        http_error_msg = ''
        if 400 <= self.status_code < 500:
            http_error_msg = u'%s Client Error' % self.status_code
        elif 500 <= self.status_code < 600:
            http_error_msg = u'%s Server Error' % self.status_code
        if http_error_msg:
            raise Exception(http_error_msg)

    def json(self):
        return self.json_data


def mock_api_site_validator_success(url, *args, **kwargs):
    if url == 'http://dataset_url':
        return MockResponse({}, 200)
    elif url == 'http://ckanapi_url':
        return MockResponse({'success': True}, 200)
    else:
        return MockResponse({'success': True}, 200)


def mock_api_site_validator_fail(url, *args, **kwargs):
    if url == 'http://dataset_url':
        return MockResponse({}, 400)
    elif url == 'http://ckanapi_url':
        return MockResponse({'success': False}, 200)
    else:
        return MockResponse({}, 404)


class SitesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(SitesTest, cls).setUpClass()
        User.objects.create_superuser(
            'test_admin', 'myemail@test.com', 'test_admin')
        site = Site.objects.create(
            title='test', dataset_url='http://dataset_url', ckanapi_url='http://ckanapi_url')
        cls.site_pk = site.pk

    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')
        self.package_list_url = reverse("package_list")
        self.package_show = reverse("package_show")
        self.package_search = "{0}?{1}".format(
            reverse("package_search"), urlencode({'q': "(消費%20AND%20平成28)"}))
        self.stat = reverse("stat")

    def test_index_get(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_list.html')

    def test_package_list_get(self):
        response = self.client.get(self.package_list_url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual("success" in content, True)

    def test_package_show_get(self):
        response = self.client.get(self.package_show)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual("success" in content, True)

    def test_package_search_get(self):
        response = self.client.get(self.package_search)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual("success" in content, True)

    def test_stat_get(self):
        response = self.client.get(self.stat)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual("success" in content, True)

    @mock.patch('sites.views.requests.sessions.Session.get', side_effect=mock_api_site_validator_success)
    def test_validate_site_success(self, mock_req_session_get):
        self.client.login(username='test_admin', password='test_admin')
        resp = self.client.get(
            reverse('site-validate', kwargs={'pk': self.site_pk}))
        result = resp.json()
        self.assertTrue(result['dataset_url']['success'])
        self.assertTrue(result['ckanapi_url']['success'])
        self.assertTrue(result['fq']['success'])

    @mock.patch('sites.views.requests.sessions.Session.get', side_effect=mock_api_site_validator_fail)
    def test_validate_site_fail(self, mock_req_session_get):
        self.client.login(username='test_admin', password='test_admin')
        resp = self.client.get(
            reverse('site-validate', kwargs={'pk': self.site_pk}))
        result = resp.json()
        self.assertFalse(result['dataset_url']['success'])
        self.assertFalse(result['ckanapi_url']['success'])
        self.assertFalse(result['fq']['success'])

    @mock.patch('sites.views.requests.sessions.Session.get')
    def test_validate_site_401(self, mock_req_session_get):
        mock_req_session_get.return_value = MockResponse({}, 401)
        resp = self.client.get(
            reverse('site-validate', kwargs={'pk': self.site_pk}))
        result = resp.json()
        self.assertEqual(resp.status_code, 401)
        self.assertDictEqual(result['dataset_url'], {})
        self.assertDictEqual(result['ckanapi_url'], {})
        self.assertDictEqual(result['fq'], {})

    def test_site_import_success(self):
        self.client.login(username='test_admin', password='test_admin')
        data = io.BytesIO('[{"id": 7, "title": "test", "dataset_url": "https://opendata.pref.aomori.lg.jp/dataset/", "ckanapi_url": "https://opendata.pref.aomori.lg.jp/api/", "proxy_url": "http://search.ckan.jp/backend/api/", "is_fq_available": true, "update_start_datetime": "2021-06-20T08:11:17Z", "update_interval": "PT1H", "result": true, "update_time": "2021-06-21T08:11:17Z", "executed_at": "2021-06-21T07:43:22.791Z", "full_update_start_datetime": "2021-06-20T07:11:21Z", "full_update_interval": "PT1H", "full_result": true, "full_update_time": "2021-06-21T08:11:21Z", "full_executed_at": "2021-06-21T07:43:25.866Z", "contact": null, "publisher": null, "publisher_url": "http://sizuoka.com", "enable": true, "memo": "OK"}]'.encode('utf-8'))
        resp = self.client.post(reverse('site-import'), {'files': data})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/sites/')
        self.assertTrue(len(Site.objects.all()) > 1)

    def test_site_import_401(self):
        resp = self.client.post(reverse('site-import'), {'files': ''})
        self.assertEqual(resp.status_code, 401)

    def test_site_import_400(self):
        self.client.login(username='test_admin', password='test_admin')
        resp = self.client.post(reverse('site-import'), {'files': ''})
        self.assertEqual(resp.status_code, 400)

    def test_site_export_success(self):
        self.client.login(username='test_admin', password='test_admin')
        resp = self.client.get(reverse('site-export'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers['Content-Disposition'], 'attachment; filename=export.json')
        self.assertTrue(len(resp.json()) > 0)

    def test_site_export_401(self):
        resp = self.client.get(reverse('site-export'))
        self.assertEqual(resp.status_code, 401)
