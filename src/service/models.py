from django.contrib.auth import get_user_model

from service.sub_models.characteristics import (
    CalculatedCharacteristic,
    SupportedCharacteristic,
)
from service.sub_models.goal import Equalizer, Goal

# Do not delete this imports
from service.sub_models.measures import CalculatedMeasure, SupportedMeasure
from service.sub_models.metrics import CollectedMetric, SupportedMetric
from service.sub_models.pre_config import PreConfig
from service.sub_models.sqc import SQC
from service.sub_models.subcharacteristics import (
    CalculatedSubCharacteristic,
    SupportedSubCharacteristic,
)

User = get_user_model()
