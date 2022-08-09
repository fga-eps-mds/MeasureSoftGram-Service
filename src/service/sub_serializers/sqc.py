from rest_framework import serializers

from service import models


class SQCSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as medidas calculadas
    """
    class Meta:
        model = models.SQC
        fields = (
            'id',
            'value',
            'created_at',
        )
