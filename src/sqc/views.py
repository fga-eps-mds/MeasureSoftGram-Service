from characteristics.models import SupportedCharacteristic
from measures.models import SupportedMeasure
from metrics.models import SupportedMetric
from organizations.models import Product, Repository
from resources import calculate_sqc
from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from sqc.models import SQC
from sqc.serializers import SQCCalculationRequestSerializer, SQCSerializer
from utils.exceptions import CharacteristicNotDefinedInPreConfiguration


class LatestCalculatedSQCViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SQCSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_queryset(self):
        repository = self.get_repository()
        return repository.calculated_sqcs.all()

    def list(self, request, *args, **kwargs):
        repository = self.get_repository()
        latest_sqc = repository.calculated_sqcs.first()
        serializer = self.get_serializer(latest_sqc)
        return Response(serializer.data)


class CalculatedSQCHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """
    serializer_class = SQCSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_queryset(self):
        repository = get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )
        return repository.calculated_sqcs.all().reverse()


class CalculateSQC(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SQCSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_product(self):
        return get_object_or_404(
            Product,
            id=self.kwargs['product_pk'],
            organization_id=self.kwargs['organization_pk'],
        )

    def create(self, request, *args, **kwargs):
        serializer = SQCCalculationRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        created_at = serializer.validated_data['created_at']

        repository: Repository = self.get_repository()
        pre_config = repository.product.pre_configs.first()

        product = self.get_product()
        pre_config = product.pre_configs.first()

        # 2. Get queryset
        # TODO: Gambiarra, modelar model para nível acima
        characteristics_keys = [
            characteristic['key']
            for characteristic in pre_config.data['characteristics']
        ]
        qs = SupportedCharacteristic.objects.filter(
            key__in=characteristics_keys
        ).prefetch_related(
            'calculated_characteristics'
        ).first()

        chars_params = []
        try:
            chars_params = qs.get_latest_characteristics_params(
                pre_config,
            )
        except CharacteristicNotDefinedInPreConfiguration as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        core_params = {
            'sqc': {
                'key': 'sqc',
                'characteristics': chars_params,
            }
        }

        calculate_response = calculate_sqc(core_params)

        if calculate_response.get('code'):
            status_code = calculate_response.pop('code')
            return calculate_response(calculate_response, status=status_code)

        data = calculate_response['sqc'][0]

        sqc = SQC.objects.create(
            repository=repository,
            value=data['value'],
            created_at=created_at,
        )

        serializer = SQCSerializer(sqc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
