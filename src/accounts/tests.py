from django.contrib.auth import get_user_model

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from utils.tests import APITestCaseExpanded

User = get_user_model()


class AccountsViews(APITestCaseExpanded):

    def setUp(self):
        self.user = User.objects.create(
            username='Test-User', first_name='Test',
            last_name='User', email='test_user@email.com'
        )

    def test_logout_acccount(self):
        token = Token.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user, token=token)

        url = reverse('accounts-logout')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Token.objects.count(), 0)

    def test_fail_logout_without_authentication(self):
        url = reverse('accounts-logout')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
