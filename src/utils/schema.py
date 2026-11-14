from rest_framework import serializers


def record_schema(name: str, entity_field: str = None, latest: bool = False):
    """
    Serializer só de documentação para o registro calculado que os SerializerMethodField
    `latest`/`history` devolvem (sem ele o drf_yasg descreve o campo como string).

    Com `latest=True`, os campos podem faltar ou vir `null`: sem registro, `Serializer(None).data`
    devolve só os campos graváveis com `None` (e `get_current_tsqmi` devolve `{}`).
    """

    def field(field_class):
        return field_class(required=not latest, allow_null=latest)

    attrs = {"id": field(serializers.IntegerField)}
    if entity_field:
        attrs[entity_field] = field(serializers.IntegerField)
    attrs["value"] = field(serializers.FloatField)
    attrs["created_at"] = field(serializers.DateTimeField)
    return type(name, (serializers.Serializer,), attrs)
