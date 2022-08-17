import datetime as dt

from django.contrib import admin

from service.sub_admin.characteristics import (
    CalculatedCharacteristicAdmin,
    SupportedCharacteristicAdmin,
)
from service.sub_admin.goal import GoalAdmin

# Do not delete this imports
from service.sub_admin.measures import CalculatedMeasureAdmin, SupportedMeasureAdmin
from service.sub_admin.metrics import CollectedMetricAdmin, SupportedMetricAdmin
from service.sub_admin.pre_config import PreConfigAdmin
from service.sub_admin.subcharacteristics import (
    CalculatedSubCharacteristicAdmin,
    SupportedSubCharacteristicAdmin,
)
