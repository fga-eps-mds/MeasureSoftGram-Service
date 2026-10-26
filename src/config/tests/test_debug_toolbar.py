import types
from unittest import mock

from django.test import RequestFactory, SimpleTestCase

from config.debug_toolbar import show_toolbar_for_pages

AXIOS_ACCEPT = "application/json, text/plain, */*"
BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


class ShowToolbarForPagesTestCase(SimpleTestCase):
    def request(self, accept):
        return RequestFactory().get("/api/v1/organizations/", HTTP_ACCEPT=accept)

    @mock.patch("config.debug_toolbar._default_show_toolbar", return_value=True)
    def test_shows_on_html_pages(self, _):
        self.assertTrue(show_toolbar_for_pages(self.request(BROWSER_ACCEPT)))

    @mock.patch("config.debug_toolbar._default_show_toolbar", return_value=True)
    def test_skips_json_calls_from_the_front(self, default):
        self.assertFalse(show_toolbar_for_pages(self.request(AXIOS_ACCEPT)))
        # nem chega a consultar a regra padrão do toolbar
        default.assert_not_called()

    @mock.patch("config.debug_toolbar._default_show_toolbar", return_value=False)
    def test_keeps_the_default_rule_for_html(self, _):
        # sem DEBUG ou fora dos IPs internos, a regra padrão do toolbar continua valendo
        self.assertFalse(show_toolbar_for_pages(self.request(BROWSER_ACCEPT)))

    def test_uses_the_default_rule_of_the_toolbar(self):
        # o módulo de verdade só importa com o debug_toolbar em INSTALLED_APPS (settings de dev)
        default_rule = mock.Mock(return_value=True)
        fake_middleware = types.SimpleNamespace(show_toolbar=default_rule)
        request = self.request(BROWSER_ACCEPT)

        with mock.patch.dict("sys.modules", {"debug_toolbar.middleware": fake_middleware}):
            self.assertTrue(show_toolbar_for_pages(request))

        default_rule.assert_called_once_with(request)
