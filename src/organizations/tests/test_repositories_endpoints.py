from unittest import mock

from rest_framework.reverse import reverse

from characteristics.models import SupportedCharacteristic
from measures.models import SupportedMeasure
from metrics.models import SupportedMetric
from organizations.models import Repository
from subcharacteristics.models import SupportedSubCharacteristic
from utils.mocks import Mocks
from utils.tests import APITestCaseExpanded


class RepositoriesViewsSetCase(APITestCaseExpanded):

    def test_create_a_new_repository(self):
        data = {
            'name': 'Test Repository',
            'description': 'Test Repository Description',
        }
        org = self.get_organization()
        product = self.get_product(org)
        url = reverse('repository-list', args=[org.id, product.id])
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data['name'], 'Test Repository')
        self.assertEqual(data['description'], 'Test Repository Description')

        qs = Repository.objects.filter(name='Test Repository')

        self.assertEqual(qs.exists(), True)
        self.assertEqual(qs.count(), 1)

        repository = qs.first()

        self.assertEqual(repository.name, "Test Repository")
        self.assertEqual(repository.description, "Test Repository Description")

        self.assertEqual(repository.product, product)
        self.assertEqual(repository.product.organization, org)

        url = reverse('repository-list', args=[org.id, product.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        repo = data['results'][0]

        self.assertEqual(data['count'], 1)
        self.assertEqual(repo['name'], 'Test Repository')
        self.assertEqual(repo['description'], 'Test Repository Description')

    def test_if_existing_repositories_is_being_listed(self):
        org = self.get_organization()
        product = self.get_product(org)
        self.get_repository(product, name="Test Repository 2")
        self.get_repository(product, name="Test Repository 1")

        url = reverse('repository-list', args=[org.id, product.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['count'], 2)

        repo1 = data['results'][0]
        repo2 = data['results'][1]

        self.assertEqual(repo1['name'], 'Test Repository 1')
        self.assertEqual(repo1['description'], 'Test Repository Description')

        self.assertEqual(repo2['name'], 'Test Repository 2')
        self.assertEqual(repo2['description'], 'Test Repository Description')

    def test_if_only_product_repositories_is_beign_listed(self):
        org1 = self.get_organization()

        prod1 = self.get_product(
            org1,
            name="Test Product 1",
            description="Test Product Description 1",
        )

        prod2 = self.get_product(
            org1,
            name="Test Product 2",
            description="Test Product Description 2",
        )

        self.get_repository(prod1, name="Test Repository 1")
        self.get_repository(prod1, name="Test Repository 2")
        self.get_repository(prod2, name="Test Repository 3")

        url = reverse('repository-list', args=[org1.id, prod1.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['name'], 'Test Repository 2')
        self.assertEqual(data['results'][1]['name'], 'Test Repository 1')

    def test_update_a_existing_repository(self):
        org = self.get_organization()
        product = self.get_product(org)
        repository = self.get_repository(product)

        data = {
            'name': 'Test Repository Updated',
            'description': 'Test Repository Description Updated',
        }

        url = reverse('repository-detail', args=[org.id, product.id, repository.id])
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['name'], 'Test Repository Updated')
        self.assertEqual(data['description'], 'Test Repository Description Updated')

        qs = Repository.objects.filter(name='Test Repository Updated')

        self.assertEqual(qs.exists(), True)
        self.assertEqual(qs.count(), 1)

        repository = qs.first()

        self.assertEqual(repository.name, "Test Repository Updated")
        self.assertEqual(repository.description, "Test Repository Description Updated")

        self.assertEqual(repository.product, product)
        self.assertEqual(repository.product.organization, org)

        url = reverse('repository-detail', args=[org.id, product.id, repository.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['name'], 'Test Repository Updated')
        self.assertEqual(data['description'], 'Test Repository Description Updated')

    def test_delete_a_existing_repository(self):
        org = self.get_organization()
        product = self.get_product(org)
        repository = self.get_repository(product)

        url = reverse('repository-detail', args=[org.id, product.id, repository.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, 204)

        qs = Repository.objects.filter(name='Test Repository')

        self.assertEqual(qs.exists(), False)
        self.assertEqual(qs.count(), 0)

        url = reverse('repository-detail', args=[org.id, product.id, repository.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 404)

        url = reverse('repository-list', args=[org.id, product.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['count'], 0)

    def test_if_repository_attribute_key_is_being_set(self):
        org = self.get_organization()
        product = self.get_product(org)
        repository = self.get_repository(product, name="ração-backend")

        url = reverse('repository-detail', args=[org.id, product.id, repository.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        key = response.json()['key']

        self.assertEqual(key, 'racao-backend')
        self.assertEqual(repository.key, 'racao-backend')

    def get_repository_urls(self, url_group):
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        url = reverse(
            'repository-detail',
            args=[
                self.org.id,
                self.product.id,
                self.repository.id
            ],
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        return data[url_group]

    def test_if_latest_metric_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('latest_values')
        metrics_url = latest_values_urls['metrics']
        response = self.client.get(metrics_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_latest_measures_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('latest_values')
        measures_url = latest_values_urls['measures']
        response = self.client.get(measures_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_latest_subcharacteristics_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('latest_values')
        subcharacteristics_url = latest_values_urls['subcharacteristics']
        response = self.client.get(subcharacteristics_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_latest_characteristics_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('latest_values')
        characteristics_url = latest_values_urls['characteristics']
        response = self.client.get(characteristics_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_latest_sqc_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('latest_values')
        sqc_url = latest_values_urls['sqc']
        response = self.client.get(sqc_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_historical_metrics_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('historical_values')
        metrics_url = latest_values_urls['metrics']
        response = self.client.get(metrics_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_historical_measures_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('historical_values')
        measures_url = latest_values_urls['measures']
        response = self.client.get(measures_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_historical_subcharacteristics_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('historical_values')
        subcharacteristics_url = latest_values_urls['subcharacteristics']
        response = self.client.get(subcharacteristics_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_historical_characteristics_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('historical_values')
        characteristics_url = latest_values_urls['characteristics']
        response = self.client.get(characteristics_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_historical_sqc_values_action_url_is_working(self):
        latest_values_urls = self.get_repository_urls('historical_values')
        sqc_url = latest_values_urls['sqc']
        response = self.client.get(sqc_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_collect_metric_action_url_is_working(self):
        actions_urls = self.get_repository_urls('actions')
        url = actions_urls['collect metric']
        metric_id = SupportedMetric.objects.first().id
        data = {'metric_id': metric_id, 'value': 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    @mock.patch(
        "utils.clients.core_service.CoreClient.calculate_measure",
        side_effect=Mocks.calculate_measure,
    )
    def test_if_calculate_measures_action_url_is_working(self, *a, **k):
        actions_urls = self.get_repository_urls('actions')
        url = actions_urls['calculate measures']
        measures_keys = [
            {'key': measure.key}
            for measure in SupportedMeasure.objects.all()
        ]
        data = {'measures': measures_keys}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    @mock.patch(
        "utils.clients.core_service.CoreClient.calculate_subcharacteristic",
        side_effect=Mocks.calculate_subcharacteristic,
    )
    def test_if_calculate_subcharacteristics_action_url_is_working(self, *a, **k):
        actions_urls = self.get_repository_urls('actions')
        url = actions_urls['calculate subcharacteristics']
        pre_config = self.product.pre_configs.first()
        qs = pre_config.get_subcharacteristics_qs()
        keys = [{'key': subcharacteristic.key} for subcharacteristic in qs]
        data = {'subcharacteristics': keys}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    @mock.patch(
        "utils.clients.core_service.CoreClient.calculate_characteristic",
        side_effect=Mocks.calculate_characteristic,
    )
    def test_if_calculate_characteristics_action_url_is_working(self, *a, **k):
        actions_urls = self.get_repository_urls('actions')
        url = actions_urls['calculate characteristics']
        pre_config = self.product.pre_configs.first()
        qs = pre_config.get_characteristics_qs()
        keys = [{'key': characteristic.key} for characteristic in qs]
        data = {'characteristics': keys}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    @mock.patch(
        "utils.clients.core_service.CoreClient.calculate_sqc",
        side_effect=Mocks.calculate_sqc,
    )
    def test_if_calculate_sqc_action_url_is_working(self, *a, **k):
        actions_urls = self.get_repository_urls('actions')
        url = actions_urls['calculate sqc']
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)

    def test_if_is_not_allowed_to_create_repositories_with_same_name(self):
        data = {
            'name': 'Test Repository',
            'description': 'Test Repository Description',
        }
        org = self.get_organization()
        product = self.get_product(org)
        url = reverse('repository-list', args=[org.id, product.id])

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
