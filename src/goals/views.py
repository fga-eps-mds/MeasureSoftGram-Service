from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from goals.models import Goal
from goals.serializers import GoalSerializer

from organizations.models import Product


class CurrentGoalModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def list(self, request, *args, **kwargs):
        # first() == mais recente == goal atual
        latest_goal = Goal.objects.first()
        serializer = GoalSerializer(latest_goal)
        return Response(serializer.data, status.HTTP_200_OK)


class CreateGoalModelViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = GoalSerializer

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product,
            id=self.kwargs['product_pk'],
        )
        serializer.save(product=product)
