from django.contrib.auth import get_user_model

# Do not delete this imports
from service.sub_models.metrics import (
    CollectedMetric,
    SupportedMetric,
)

# Do not delete this imports
from service.sub_models.measures import (
    SupportedMeasure,
    CalculatedMeasure,
)

User = get_user_model()


