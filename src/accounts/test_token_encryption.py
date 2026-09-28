from uuid import uuid4

import pytest
from allauth.socialaccount.models import SocialAccount, SocialLogin, SocialToken
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from accounts.adapters import EncryptedTokenSocialAccountAdapter
from accounts.fields import TOKEN_PREFIX, decrypt_token, encrypt_token
from accounts.models import CustomUser
from accounts.signals import save_github_token


def stored_token(user):
    with connection.cursor() as cursor:
        cursor.execute("SELECT github_access_token FROM accounts_customuser WHERE id = %s", [user.pk])
        return cursor.fetchone()[0]


class TokenEncryptionTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="alice", email="alice@example.com")

    def test_signal_encrypts_database_value_and_orm_decrypts_it(self):
        account = SocialAccount(provider="github", uid="123")
        sociallogin = SocialLogin(
            user=self.user,
            account=account,
            token=SocialToken(account=account, token="github-sensitive-token"),
        )
        save_github_token(None, sociallogin)
        raw = stored_token(self.user)
        self.assertTrue(raw.startswith(TOKEN_PREFIX))
        self.assertNotIn("github-sensitive-token", raw)
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_access_token, "github-sensitive-token")
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_access_token, "github-sensitive-token")
        self.assertNotEqual(raw, stored_token(self.user))

    def test_first_social_signup_saves_encrypted_token(self):
        account = SocialAccount(provider="github", uid="456")
        sociallogin = SocialLogin(
            user=CustomUser(username="new-user", email="new@example.com"),
            account=account,
            token=SocialToken(account=account, token="first-login-token"),
        )
        request = RequestFactory().post("/api/v1/accounts/github/login/")
        request.session = {}
        user = EncryptedTokenSocialAccountAdapter().save_user(request, sociallogin)
        self.assertNotEqual(stored_token(user), "first-login-token")
        user.refresh_from_db()
        self.assertEqual(user.github_access_token, "first-login-token")
        self.assertFalse(SocialToken.objects.filter(account__user=user).exists())

    def test_update_and_bulk_create_encrypt(self):
        CustomUser.objects.filter(pk=self.user.pk).update(github_access_token="updated-token")
        self.assertEqual(decrypt_token(stored_token(self.user)), "updated-token")
        user = CustomUser(username="bulk", email="bulk@example.com", github_access_token="bulk-token")
        CustomUser.objects.bulk_create([user])
        user = CustomUser.objects.get(username="bulk")
        self.assertEqual(user.github_access_token, "bulk-token")
        self.assertNotEqual(stored_token(user), "bulk-token")

    def test_null_and_empty_tokens_remain_empty(self):
        for value in (None, ""):
            with self.subTest(value=value):
                self.user.github_access_token = value
                self.user.save()
                self.user.refresh_from_db()
                self.assertEqual(self.user.github_access_token, value)
                self.assertEqual(stored_token(self.user), value)

    def test_ciphertext_supports_tokens_longer_than_old_column(self):
        self.user.github_access_token = "x" * 255
        self.user.save()
        self.assertGreater(len(stored_token(self.user)), 255)
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_access_token, "x" * 255)

    def test_invalid_or_missing_key_fails_without_plaintext_write(self):
        for keys in ([], ["invalid-key"]):
            with self.subTest(keys=keys), override_settings(GITHUB_TOKEN_ENCRYPTION_KEYS=keys):
                with self.assertRaises(ImproperlyConfigured), transaction.atomic():
                    CustomUser.objects.filter(pk=self.user.pk).update(github_access_token="sensitive")
        self.assertIsNone(stored_token(self.user))

    def test_wrong_key_tampering_and_plaintext_are_rejected(self):
        encrypted = encrypt_token("sensitive")
        with override_settings(GITHUB_TOKEN_ENCRYPTION_KEYS=[Fernet.generate_key().decode()]):
            with self.assertRaises(InvalidToken):
                decrypt_token(encrypted)
        for value in ("plaintext-legacy-token", encrypted[:-8] + "AAAAAAAA"):
            with self.assertRaises(InvalidToken):
                decrypt_token(value)

    def test_key_rotation_reads_old_tokens_and_writes_with_new_key(self):
        old_value = encrypt_token("sensitive")
        new_key = Fernet.generate_key().decode()
        with override_settings(GITHUB_TOKEN_ENCRYPTION_KEYS=[new_key, *settings.GITHUB_TOKEN_ENCRYPTION_KEYS]):
            self.assertEqual(decrypt_token(old_value), "sensitive")
            new_value = encrypt_token("sensitive")
        self.assertEqual(Fernet(new_key).decrypt(new_value[len(TOKEN_PREFIX) :]), b"sensitive")

    def test_admin_form_does_not_expose_token(self):
        request = RequestFactory().get("/admin/accounts/customuser/")
        request.user = self.user
        form = admin.site._registry[CustomUser].get_form(request)
        self.assertNotIn("github_access_token", form.base_fields)

    def test_missing_oauth_token_does_not_erase_existing_token(self):
        self.user.github_access_token = "keep-me"
        self.user.save()
        sociallogin = SocialLogin(user=self.user, account=SocialAccount(provider="github", uid="123"))
        save_github_token(None, sociallogin)
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_access_token, "keep-me")


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_migration_encrypts_legacy_tokens_and_removes_plaintext_copies(tmp_path, backend):
    # A separate database lets us exercise the irreversible migration from scratch.
    alias = "token_migration"
    config = connections.databases["default"].copy()
    if backend == "sqlite":
        config.update(ENGINE="django.db.backends.sqlite3", NAME=str(tmp_path / "migration.sqlite3"), OPTIONS={})
    else:
        if connection.vendor != "postgresql":
            pytest.skip("PostgreSQL migration validation requires the PostgreSQL test settings.")
        config["NAME"] = "test_token_migration_" + uuid4().hex
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE {connection.ops.quote_name(config["NAME"])}')
    connections.databases[alias] = config
    db = connections[alias]
    # Django 5.2 records allowed aliases during test setup. Register this
    # deliberately isolated alias in pytest-django's temporary test class.
    for cell in db.ensure_connection.__func__.__closure__ or ():
        test_class = cell.cell_contents
        if isinstance(test_class, type) and issubclass(test_class, SimpleTestCase):
            test_class.databases = frozenset((*test_class.databases, alias))
    try:
        before = [("accounts", "0002_customuser_github_access_token"), ("socialaccount", "0001_initial")]
        executor = MigrationExecutor(db)
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        User = apps.get_model("accounts", "CustomUser")
        Account = apps.get_model("socialaccount", "SocialAccount")
        App = apps.get_model("socialaccount", "SocialApp")
        Token = apps.get_model("socialaccount", "SocialToken")
        app = App.objects.using(alias).create(provider="github", name="GitHub", client_id="test", secret="test")
        for name, value in [("plain", "legacy-token"), ("fallback", None), ("empty", ""), ("null", None)]:
            user = User.objects.using(alias).create(
                username=name, email=f"{name}@example.com", github_access_token=value
            )
            if name in ("plain", "fallback"):
                account = Account.objects.using(alias).create(user_id=user.pk, provider="github", uid=name)
                Token.objects.using(alias).create(account_id=account.pk, app_id=app.pk, token="legacy-social-token")
        after = [("accounts", "0003_encrypt_github_access_token")]
        executor = MigrationExecutor(db)
        with override_settings(GITHUB_TOKEN_ENCRYPTION_KEYS=[]), pytest.raises(ImproperlyConfigured):
            executor.migrate(after)
        assert User.objects.using(alias).get(username="plain").github_access_token == "legacy-token"
        executor = MigrationExecutor(db)
        executor.migrate(after)
        for name, expected in [
            ("plain", "legacy-token"),
            ("fallback", "legacy-social-token"),
            ("empty", ""),
            ("null", None),
        ]:
            assert CustomUser.objects.using(alias).get(username=name).github_access_token == expected
            with db.cursor() as cursor:
                cursor.execute("SELECT github_access_token FROM accounts_customuser WHERE username = %s", [name])
                raw = cursor.fetchone()[0]
            assert decrypt_token(raw) == expected
            if expected:
                assert raw != expected
        assert not Token.objects.using(alias).exists()
        # Applying the same migration plan again must not double-encrypt values.
        MigrationExecutor(db).migrate(after)
        assert CustomUser.objects.using(alias).get(username="plain").github_access_token == "legacy-token"
    finally:
        db.close()
        del connections[alias]
        del connections.databases[alias]
        if backend == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute(f'DROP DATABASE {connection.ops.quote_name(config["NAME"])}')
