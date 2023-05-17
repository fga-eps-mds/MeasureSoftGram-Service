from organizations.routers.routers import Router
import organizations.views as views

class OrgRouter(Router):

    
    def __init__(self, parent_router, **children):
        super().__init__(
            parent_router,
            'organizations', 
            'organization', 
            children=[
                {'name': 'products', 'view': views.ProductViewSet, 'basename': ''},
                *children
        ])

