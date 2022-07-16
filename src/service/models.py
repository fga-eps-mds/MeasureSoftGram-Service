from django.contrib.auth import get_user_model

# Do not delete this imports
from service.sub_models.metrics import (
    CollectedMetric,
    SupportedMetric,
)

User = get_user_model()


