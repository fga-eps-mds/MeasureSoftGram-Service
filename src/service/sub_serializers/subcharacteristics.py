from rest_framework import serializers

from service import models


class SupportedSubCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma subcaracterística suportada
    """
    class Meta:
        model = models.SupportedSubCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
        )
