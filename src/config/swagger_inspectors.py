from drf_yasg import openapi
from drf_yasg.inspectors import ReferencingSerializerInspector


class NullableReferencingSerializerInspector(ReferencingSerializerInspector):
    """
    Serializer aninhado com `allow_null=True` sai como `$ref` sem `x-nullable` no drf_yasg.
    O E2E do Front valida as respostas contra o schema e lê `x-nullable` ao lado do `$ref`.
    """

    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        result = super().field_to_swagger_object(field, swagger_object_type, use_references, **kwargs)
        if isinstance(result, openapi.SchemaRef) and getattr(field, "allow_null", False):
            # SchemaRef só aceita a chave $ref
            nullable = openapi.SwaggerDict()
            dict.__setitem__(nullable, "$ref", result.ref)
            dict.__setitem__(nullable, "x-nullable", True)
            return nullable
        return result
