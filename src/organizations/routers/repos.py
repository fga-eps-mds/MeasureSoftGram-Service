from organizations.routers.routers import Router

from collectors.github.view import ImportGithubMetricsViewSet

from collectors.sonarqube.view import ImportSonarQubeMetricsViewSet

from measures.views import (
    CalculatedMeasureHistoryModelViewSet,
    CalculateMeasuresViewSet,
    LatestCalculatedMeasureModelViewSet,
    SupportedMeasureModelViewSet,
)
from metrics.views import (
    CollectedMetricHistoryModelViewSet,
    CollectedMetricModelViewSet,
    LatestCollectedMetricModelViewSet,
    SupportedMetricModelViewSet,
)
from characteristics.views import (
    CalculateCharacteristicViewSet,
    CalculatedCharacteristicHistoryModelViewSet,
    LatestCalculatedCharacteristicModelViewSet,
    SupportedCharacteristicModelViewSet,
)
from sqc.views import (
    CalculatedSQCHistoryModelViewSet,
    CalculateSQC,
    LatestCalculatedSQCViewSet,
)
from subcharacteristics.views import (
    CalculatedSubCharacteristicHistoryModelViewSet,
    CalculateSubCharacteristicViewSet,
    LatestCalculatedSubCharacteristicModelViewSet,
    SupportedSubCharacteristicModelViewSet,
)

import organizations.views as views


class RepoRouter(Router):
    def __init__(self, parent_router, **children):
        super().__init__(
            parent_router,
            'repositories',
            'repository',
            children=[
                *self._get_actions_endpoints_dicts(),
                *self._get_latest_values_endpoints_dict(),
                *self._get_historic_values_endpoints_dicts(),
                *self._get_collectors_endpoints_dict(),
                *children,
            ],
        )

    def _get_actions_endpoints_dicts(self):
        return [
            {
                'name': 'collect/metrics',
                'view': CollectedMetricModelViewSet,
                'basename': '',
            },
            {
                'name': 'calculate/measures',
                'view': CalculateMeasuresViewSet,
                'basename': 'calculate-measures',
            },
            {
                'name': 'calculate/subcharacteristics',
                'view': CalculateSubCharacteristicViewSet,
                'basename': 'calculate-subcharacteristics',
            },
            {
                'name': 'calculate/characteristics',
                'view': CalculateCharacteristicViewSet,
                'basename': 'calculate-characteristics',
            },
            {
                'name': 'calculate/sqc',
                'view': CalculateSQC,
                'basename': 'calculate-sqc',
            },
        ]

    def _get_latest_values_endpoints_dict(self):
        return [
            {
                'name': 'latest-values/metrics',
                'view': LatestCollectedMetricModelViewSet,
                'basename': 'latest-collected-metrics',
            },
            {
                'name': 'latest-values/measures',
                'view': LatestCalculatedMeasureModelViewSet,
                'basename': 'latest-calculated-measures',
            },
            {
                'name': 'latest-values/subcharacteristics',
                'view': LatestCalculatedSubCharacteristicModelViewSet,
                'basename': 'latest-calculated-subcharacteristics',
            },
            {
                'name': 'latest-values/characteristics',
                'view': LatestCalculatedCharacteristicModelViewSet,
                'basename': 'latest-calculated-characteristics',
            },
            {
                'name': 'latest-values/sqc',
                'view': LatestCalculatedSQCViewSet,
                'basename': 'latest-calculated-sqc',
            },
        ]

    def _get_historic_values_endpoints_dicts(self):
        return [
            {
                'name': 'historical-values/metrics',
                'view': CollectedMetricHistoryModelViewSet,
                'basename': 'metrics-historical-values',
            },
            {
                'name': 'historical-values/measures',
                'view': CalculatedMeasureHistoryModelViewSet,
                'basename': 'measures-historical-values',
            },
            {
                'name': 'historical-values/subcharacteristics',
                'view': CalculatedSubCharacteristicHistoryModelViewSet,
                'basename': 'subcharacteristics-historical-values',
            },
            {
                'name': 'historical-values/characteristics',
                'view': CalculatedCharacteristicHistoryModelViewSet,
                'basename': 'characteristics-historical-values',
            },
            {
                'name': 'historical-values/sqc',
                'view': CalculatedSQCHistoryModelViewSet,
                'basename': 'sqc-historical-values',
            },
        ]

    def _get_collectors_endpoints_dict(self):
        return [
            {
                'name': 'collectors/github',
                'view': ImportGithubMetricsViewSet,
                'basename': 'github-collector',
            },
            {
                'name': 'collectors/sonarqube',
                'view': ImportSonarQubeMetricsViewSet,
                'basename': 'sonarqube-collector',
            },
        ]
