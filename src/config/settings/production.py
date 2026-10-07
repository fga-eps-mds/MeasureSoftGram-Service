"""
Production settings — DJANGO_SETTINGS_MODULE=config.settings.production

HTTPS obrigatorio. O proxy de borda deve terminar TLS e sobrescrever
X-Forwarded-Proto; o proxy interno so pode receber trafego dessa borda.
Veja docs/seguranca.md antes do deploy.
"""

import os

from .base import *  # noqa: F401,F403


def _env_flag(name, default="False"):
    return os.getenv(name, default).lower() in ("true", "t", "1", "yes")


DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_flag("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False")
SECURE_HSTS_PRELOAD = _env_flag("SECURE_HSTS_PRELOAD", "False")

# Atras de proxy: confiar no header X-Forwarded-Proto pra detectar https
# quando o TLS termina na borda. So tem efeito se o proxy setar o header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Healthcheck interno sem credenciais; demais rotas exigem HTTPS.
SECURE_REDIRECT_EXEMPT = [r"^health/$"]

USE_X_FORWARDED_HOST = _env_flag("USE_X_FORWARDED_HOST", "False")

# Clickjacking
X_FRAME_OPTIONS = "DENY"

# CREATE_FAKE_DATA: desligado por default (producao real fica limpa), mas
# pode ser ligado via env var para deploys de demonstracao/homologacao.
CREATE_FAKE_DATA = _env_flag("CREATE_FAKE_DATA", "False")

# (MSG-16) Origens permitidas em producao: Dominio canonico + Variaveis de Ambiente
# A leitura dinamica das variaveis CORS_ALLOWED_ORIGINS e CSRF_TRUSTED_ORIGINS ja ocorre no base.py
CORS_ALLOWED_ORIGINS.append("https://msgram.lappis.rocks")  # noqa: F405
CSRF_TRUSTED_ORIGINS.append("https://msgram.lappis.rocks")  # noqa: F405
