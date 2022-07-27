from django.contrib import admin, messages

from service import models


@admin.register(models.SupportedCharacteristic)
class SupportedCharacteristicAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "key",
        "name",
        "description",
    )
    search_fields = (
        "key",
        "name",
    )


@admin.register(models.SupportedCharacteristic.subcharacteristics.through)
class SubCharacteristicCharacteristicAssociation(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        msg = ((
            "Tabela que armazena a relação entre "
            "as CARACTERÍSTICAS e suas SUBCARACTERÍSTICAS."
        ))
        messages.add_message(request, messages.INFO, msg)
        return super().changelist_view(request, extra_context)

    # TODO: Descobrir como renomear essa tabela nas telas de admin
    class Meta:
        verbose_name = "SubCharacteristic Characteristic Association"
        verbose_name_plural = "SubCharacteristic Characteristic Association"

    list_display = (
        "id",
        "get_subcharacteristic_key",
        "get_characteristic_key",
    )
    search_fields = (
        "get_characteristic_key",
        "get_subcharacteristic_key",
    )
    list_filter = (
        "supportedcharacteristic",
    )

    def get_subcharacteristic_key(self, obj):
        return obj.supportedsubcharacteristic.key
    get_subcharacteristic_key.short_description = "SubCharacteristic key"
    get_subcharacteristic_key.admin_order_field = "supportedsubcharacteristic__key"

    def get_characteristic_key(self, obj):
        return obj.supportedcharacteristic.key
    get_characteristic_key.short_description = "Characteristic key"
    get_characteristic_key.admin_order_field = "supportedcharacteristic__key"
