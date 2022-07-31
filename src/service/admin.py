import datetime as dt

from django.contrib import admin

# Do not delete this imports
from service.sub_admin.characteristics import SupportedCharacteristicAdmin
from service.sub_admin.measures import CalculatedMeasureAdmin, SupportedMeasureAdmin
from service.sub_admin.metrics import CollectedMetricAdmin, SupportedMetricAdmin
from service.sub_admin.pre_config import PreConfigAdmin
from service.sub_admin.subcharacteristics import SupportedSubCharacteristicAdmin, CalculatedSubCharacteristicAdmin
