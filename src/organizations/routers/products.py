from entity_trees.views import PreConfigEntitiesRelationshipTreeViewSet
from goals.views import (
    CompareGoalsModelViewSet,
    CreateGoalModelViewSet,
    CurrentGoalModelViewSet,
    ReleaseListModelViewSet,
)
from organizations.routers.routers import Router
from organizations.views import (
    RepositoriesTSQMIHistoryViewSet,
    RepositoriesTSQMILatestValueViewSet,
    RepositoryViewSet,
)
from pre_configs.views import (
    CreatePreConfigModelViewSet,
    CurrentPreConfigModelViewSet,
)
from releases.views import CreateReleaseModelViewSet


class ProductRouter(Router):
    def __init__(self, parent_router, **children):
        super().__init__(
            parent_router,
            'products',
            'product',
            children=[
                {
                    'name': 'entity-relationship-tree',
                    'view': PreConfigEntitiesRelationshipTreeViewSet,
                    'basename': 'pre-config-entity-relationship-tree',
                },
                {
                    'name': 'repositories-tsqmi-latest-values',
                    'view': RepositoriesTSQMILatestValueViewSet,
                    'basename': 'repositories-tsqmi-latest-values',
                },
                {
                    'name': 'repositories-tsqmi-historical-values',
                    'view': RepositoriesTSQMIHistoryViewSet,
                    'basename': 'repositories-tsqmi-historical-values',
                },
                {
                    'name': 'repositories',
                    'view': RepositoryViewSet,
                    'basename': '',
                },
                *self._get_goals_endpoints_dicts(),
                *self._get_preconfigs_endpoints_dict(),
                *children,
            ],
        )

    def _get_goals_endpoints_dicts(self):
        return [
            {
                'name': 'current/goal',
                'view': CurrentGoalModelViewSet,
                'basename': 'current-goal',
            },
            {
                'name': 'create/goal',
                'view': CreateGoalModelViewSet,
                'basename': 'create-goal',
            },
            {
                'name': 'all/goal',
                'view': CompareGoalsModelViewSet,
                'basename': 'all-goal',
            },
            {
                'name': 'release',
                'view': ReleaseListModelViewSet,
                'basename': 'release-list',
            },
            {
                'name': 'create/release',
                'view': CreateReleaseModelViewSet,
                'basename': 'create-release',
            },
        ]

    def _get_preconfigs_endpoints_dict(self):
        return [
            {
                'name': 'current/pre-config',
                'view': CurrentPreConfigModelViewSet,
                'basename': 'current-pre-config',
            },
            {
                'name': 'create/pre-config',
                'view': CreatePreConfigModelViewSet,
                'basename': 'create-pre-config',
            },
        ]
