import logging

from django.test import SimpleTestCase
from drf_yasg.generators import OpenAPISchemaGenerator

from config.swagger import api_info

PRODUCT = "/organizations/{organization_pk}/products/{product_pk}/"
REPOSITORY = PRODUCT + "repositories/{repository_pk}/"

# rotas que o E2E do Front simula: o mockApi valida cada resposta contra este schema
FRONT_ROUTES = [
    ("get", PRODUCT + "entity-analysis/"),
    ("get", PRODUCT + "entity-analysis/entities/"),
    ("get", PRODUCT + "entity-analysis/matrix/"),
    ("get", PRODUCT + "analysis-distribution/"),
    ("get", PRODUCT + "correlation/"),
    ("get", PRODUCT + "quality-model-tree/"),
    ("get", PRODUCT + "quality-bands/"),
    ("put", PRODUCT + "quality-bands/"),
    ("get", PRODUCT + "release-dashboard/summary/"),
    ("get", PRODUCT + "release-dashboard/characteristics/"),
    ("get", PRODUCT + "repositories-tsqmi-release-history/"),
    ("get", PRODUCT + "release/{id}/analysis_data/"),
    ("get", PRODUCT + "current/goal/"),
    ("get", PRODUCT + "all/goal/"),
    ("get", PRODUCT + "current/release-config/"),
    ("get", PRODUCT + "entity-relationship-tree/"),
    *[
        ("get", REPOSITORY + f"{kind}-values/{level}/")
        for kind in ("latest", "historical")
        for level in ("metrics", "measures", "subcharacteristics", "characteristics", "tsqmi")
    ],
    ("get", "/accounts/gitlab-namespaces/"),
    ("get", "/accounts/github-organizations/"),
    ("get", "/organizations/{organization_pk}/gitlab-projects/"),
    ("get", "/organizations/{organization_pk}/github-repos/"),
    ("post", "/accounts/gitlab/validate/"),
    ("post", "/accounts/github/validate/"),
]


def generate_schema():
    # sem request, como o `manage.py generate_swagger` da CI
    return OpenAPISchemaGenerator(api_info).get_schema(request=None, public=True)


def response_schema(operation):
    return next(
        (response.get("schema") for code, response in operation["responses"].items() if code.startswith("2")),
        None,
    )


class OpenAPISchemaTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema = generate_schema()

    def test_no_view_serializer_breaks_without_request(self):
        # o drf_yasg só registra no log o get_serializer que quebra sem request, e a rota sai sem schema.
        # Os avisos de get_queryset (request.user) não tiram schema: ele só deduz o tipo do parâmetro da URL.
        records = []
        handler = logging.Handler(level=logging.WARNING)
        handler.emit = records.append
        logger = logging.getLogger("drf_yasg")
        logger.addHandler(handler)
        try:
            generate_schema()
        finally:
            logger.removeHandler(handler)

        broken = [record.getMessage() for record in records if ".get_serializer" in record.getMessage()]
        self.assertEqual(broken, [])

    def test_front_routes_have_a_2xx_response_schema(self):
        missing = [
            f"{method.upper()} {path}"
            for method, path in FRONT_ROUTES
            if response_schema(self.schema["paths"][path][method]) is None
        ]
        self.assertEqual(missing, [])

    def test_method_fields_of_values_are_not_described_as_strings(self):
        definitions = self.schema["definitions"]
        for name, field in [
            ("LatestCalculatedCharacteristic", "latest"),
            ("CalculatedCharacteristicHistory", "history"),
            ("Product", "repositories"),
            ("Product", "actions"),
        ]:
            with self.subTest(definition=name, field=field):
                self.assertNotEqual(definitions[name]["properties"][field].get("type"), "string")

    def test_nullable_nested_serializer_keeps_x_nullable_next_to_ref(self):
        previous_release = self.schema["definitions"]["EntityMatrix"]["properties"]["previous_release"]
        self.assertEqual(previous_release, {"$ref": "#/definitions/ReleaseRef", "x-nullable": True})
