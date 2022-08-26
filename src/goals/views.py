from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from goals.models import Goal
from goals.serializers import GoalSerializer


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
