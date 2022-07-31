from django.contrib.auth import get_user_model

# Do not delete this imports
from service.sub_models.measures import CalculatedMeasure, SupportedMeasure
from service.sub_models.metrics import CollectedMetric, SupportedMetric
from service.sub_models.pre_config import PreConfig
from service.sub_models.subcharacteristics import SupportedSubCharacteristic, CalculatedSubCharacteristic
from service.sub_models.characteristics import SupportedCharacteristic

User = get_user_model()
