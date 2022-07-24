# Dont delete this line. It is used to import the views from the sub_views.
# Dont delete this line. It is used to import the views from the sub_views.
from service.sub_views.metrics import (
    CollectedMetricHistoryModelViewSet,
    CollectedMetricModelViewSet,
    LatestCollectedMetricModelViewSet,
    SupportedMetricModelViewSet,
)
from service.sub_views.mocked_views import (
    get_mocked_measures,
    get_mocked_measures_history,
    get_mocked_repository,
    get_specific_mocked_measure,
)

# Dont delete this line. It is used to import the views from the sub_views.
from service.sub_views.collectors.github import(
    import_github_metrics,
)

from service.sub_views.collectors.sonarqube import (
    import_sonar_metrics,
)
