from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404

from accounts.models import CustomUser
from goals.models import Goal
from organizations.models import Product

from releases.serializers import ReleaseSerializer
from releases.models import Release


class CreateReleaseModelViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReleaseSerializer
    queryset = Release.objects.all()

    def get_user(self):
        queryset = CustomUser.objects.all()
        return get_object_or_404(queryset, username=self.request.user)

    def get_product(self):
        return get_object_or_404(
            Product,
            id=self.kwargs["product_pk"],
            organization_id=self.kwargs["organization_pk"],
        )
    
    def get_goal(self):
        return get_object_or_404(Goal, id=self.request.data["goal"])
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.get_user(),
            product=self.get_product(),
            goal=self.get_goal(),
        )
