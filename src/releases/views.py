from releases.serializers import ReleaseSerializer
from releases.models import Release

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class CreateReleaseModelViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer



    def get_queryset(self):

        product_key = self.kwargs['product_pk']


        return Release.objects.filter(product=product_key)

