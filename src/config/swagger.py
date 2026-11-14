from drf_yasg import openapi

# import string em SWAGGER_SETTINGS["DEFAULT_INFO"]: o generate_swagger exige
api_info = openapi.Info(
    title="MeasureSoftGram API",
    default_version="v1",
    description="Swagger dos endpoints da API do measuresoftgram",
)
