from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.test import SimpleTestCase, override_settings
from django.urls import path

from config.settings import production


def security_probe(request):
    request.session["probe"] = True
    get_token(request)
    return HttpResponse("ok")


urlpatterns = [path("security-probe/", security_probe), path("health/", lambda request: HttpResponse("ok"))]


@override_settings(
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["testserver"],
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    SECURE_SSL_REDIRECT=production.SECURE_SSL_REDIRECT,
    SESSION_COOKIE_SECURE=production.SESSION_COOKIE_SECURE,
    CSRF_COOKIE_SECURE=production.CSRF_COOKIE_SECURE,
    SECURE_HSTS_SECONDS=production.SECURE_HSTS_SECONDS,
    SECURE_PROXY_SSL_HEADER=production.SECURE_PROXY_SSL_HEADER,
    SECURE_REDIRECT_EXEMPT=production.SECURE_REDIRECT_EXEMPT,
)
class ProductionSecurityTests(SimpleTestCase):
    def test_http_redirects_to_https_preserving_path_and_query(self):
        response = self.client.get("/security-probe/?page=2")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://testserver/security-probe/?page=2")

    def test_trusted_proxy_https_does_not_loop_and_sets_hsts(self):
        response = self.client.get("/security-probe/", HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(response.status_code, 200)
        self.assertIn("max-age=31536000", response["Strict-Transport-Security"])
        self.assertTrue(response.cookies["sessionid"]["secure"])
        self.assertTrue(response.cookies["csrftoken"]["secure"])

    def test_forwarded_http_does_not_bypass_redirect(self):
        response = self.client.get("/security-probe/", HTTP_X_FORWARDED_PROTO="http")
        self.assertEqual(response.status_code, 301)
        self.assertNotIn("Strict-Transport-Security", response)

    def test_internal_healthcheck_is_exempt_without_exempting_other_paths(self):
        self.assertEqual(self.client.get("/health/").status_code, 200)
        self.assertEqual(self.client.get("/health/other/").status_code, 301)

    def test_security_flags_are_mandatory(self):
        self.assertTrue(production.SECURE_SSL_REDIRECT)
        self.assertTrue(production.SESSION_COOKIE_SECURE)
        self.assertTrue(production.CSRF_COOKIE_SECURE)
        self.assertEqual(production.SECURE_HSTS_SECONDS, 31536000)
