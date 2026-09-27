"""Authenticated encryption for OAuth credentials stored in the database."""

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

TOKEN_PREFIX = "fernet:v1:"


def token_cipher():
    keys = settings.GITHUB_TOKEN_ENCRYPTION_KEYS
    if not keys:
        raise ImproperlyConfigured("GITHUB_TOKEN_ENCRYPTION_KEYS must contain a Fernet key.")
    try:
        return MultiFernet([Fernet(key) for key in keys])
    except (ValueError, TypeError):
        raise ImproperlyConfigured("GITHUB_TOKEN_ENCRYPTION_KEYS contains an invalid Fernet key.") from None


def encrypt_token(value):
    if value is None or value == "":
        return value
    return TOKEN_PREFIX + token_cipher().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_token(value):
    if value is None or value == "":
        return value
    if not value.startswith(TOKEN_PREFIX):
        raise InvalidToken("OAuth token is not encrypted; check the accounts migrations.")
    return token_cipher().decrypt(value[len(TOKEN_PREFIX) :].encode("ascii")).decode("utf-8")


class EncryptedTokenField(models.TextField):
    """Encrypt ORM writes and decrypt database reads; never accept plaintext from the DB."""

    def from_db_value(self, value, expression, connection):
        return decrypt_token(value)

    def get_prep_value(self, value):
        return encrypt_token(super().get_prep_value(value))
