from rest_framework.reverse import reverse

from organizations.models import Organization
from utils.tests import APITestCaseExpanded


class OrganizationsViewsTestCase(APITestCaseExpanded):

    def test_create_a_new_organization(self):
        url = reverse("organization-list")
        data = {
            "name": "Test Organization",
            "description": "Test Organization Description",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["name"], "Test Organization")
        self.assertEqual(data["description"], "Test Organization Description")

        qs = Organization.objects.filter(name="Test Organization")

        self.assertEqual(qs.exists(), True)
        self.assertEqual(qs.count(), 1)

    def compare_organization_data(self, data, org):
        self.assertEqual(data["id"], org.id)
        self.assertEqual(data["name"], org.name)
        self.assertEqual(data["description"], org.description)

    def test_if_existing_organization_is_being_listed(self):
        org = self.get_organization()
        url = reverse("organization-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()["results"]
        self.compare_organization_data(data[0], org)

    def test_update_a_existing_organization(self):
        org: Organization = self.get_organization()
        url = reverse("organization-detail", args=[org.id])
        data = {
            "name": "Test Organization Updated",
            "description": "Test Organization Description Updated",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        org = Organization.objects.get(id=org.id)
        self.compare_organization_data(data, org)

    def test_patch_update_a_existing_organization(self):
        org: Organization = self.get_organization()
        url = reverse("organization-detail", args=[org.id])
        data = {
            "description": "Test Organization Description Updated",
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        org = Organization.objects.get(id=org.id)
        self.compare_organization_data(data, org)

    def test_delete_a_existing_organization(self):
        org: Organization = self.get_organization()
        url = reverse("organization-detail", args=[org.id])
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, 204)
        qs = Organization.objects.filter(id=org.id).exists()
        self.assertEqual(qs, False)

    def test_list_all_existing_organizations(self):
        self.get_organization(name="Test Organization 1")
        self.get_organization(name="Test Organization 2")
        self.get_organization(name="Test Organization 3")

        url = reverse("organization-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data['count'], 3)
        self.assertEqual(data['next'], None)
        self.assertEqual(data['previous'], None)
        self.assertEqual(data['results'][2]['name'], "Test Organization 1")
        self.assertEqual(data['results'][1]['name'], "Test Organization 2")
        self.assertEqual(data['results'][0]['name'], "Test Organization 3")

    def test_if_attribute_key_is_being_set(self):
        """
        Testa se o atributo key está sendo setado corretamente
        "organização do dagrão!" -> "organizacao-do-dagrao"
        """
        org: Organization = self.get_organization(
            name="organização do dagrão!"
        )
        url = reverse("organization-detail", args=[org.id])
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)

        key = response.json()["key"]

        self.assertEqual(key, "organizacao-do-dagrao")
        self.assertEqual(org.key, "organizacao-do-dagrao")

    def test_if_an_organizations_product_urls_list_is_returned(self):
        org: Organization = self.get_organization()
        self.create_organization_product(org)

        url = reverse("organization-detail", args=[org.id])
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertIsInstance(data["products"], list)
        self.assertEqual(len(data["products"]), 1)

        product_url = data["products"][0]

        self.assertIsInstance(product_url, str)

        response = self.client.get(product_url, format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["name"], "Test Product")
        self.assertEqual(data["description"], "Test Product Description")

    def test_if_create_product_action_url_is_working(self):
        org: Organization = self.get_organization()
        self.create_organization_product(org)

        url = reverse("organization-detail", args=[org.id])
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        actions = data["actions"]
        create_new_product_url = actions["create a new product"]

        self.assertIsInstance(create_new_product_url, str)

        data = {
            "name": "Test Product 2",
            "description": "Test Product Description 2",
        }

        response = self.client.post(create_new_product_url, data, format="json")

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["name"], "Test Product 2")
        self.assertEqual(data["description"], "Test Product Description 2")
