from goals.views import (
    CompareGoalsModelViewSet,
    CreateGoalModelViewSet,
    CurrentGoalModelViewSet,
    ReleaseListModelViewSet,
)
from pre_configs.views import CreatePreConfigModelViewSet
from organizations.routers.routers import Router
import organizations.views as views
from entity_trees.views import PreConfigEntitiesRelationshipTreeViewSet
from pre_configs.views import CurrentPreConfigModelViewSet


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
                    'name': 'repositories-sqc-latest-values',
                    'view': views.RepositoriesSQCLatestValueViewSet,
                    'basename': 'repositories-sqc-latest-values',
                },
                {
                    'name': 'repositories-sqc-historical-values',
                    'view': views.RepositoriesSQCHistoryViewSet,
                    'basename': 'repositories-sqc-historical-values',
                },
                {
                    'name': 'repositories',
                    'view': views.RepositoryViewSet,
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
