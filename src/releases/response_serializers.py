"""
Serializers só de documentação: descrevem no schema OpenAPI os dicionários que as views
de releases montam à mão (`entity_analysis`, `entity_matrix`, `analysis_distribution`,
`correlation`, `dashboard` e o `analysis_data` da release). As views não os usam para serializar.
"""

from rest_framework import serializers

from releases.analysis_distribution import LEVELS as DISTRIBUTION_LEVELS
from releases.correlation import LEVELS as CORRELATION_LEVELS
from releases.entity_analysis import LEVELS
from releases.entity_matrix import MATRIX_LEVELS
from releases.serializers import ReleaseAllSerializer


def number(**kwargs):
    return serializers.FloatField(**kwargs)


def nullable_number():
    return serializers.FloatField(allow_null=True)


class ReleaseRefSerializer(serializers.Serializer):
    """`serialize_release`."""

    id = serializers.IntegerField()
    release_name = serializers.CharField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()


class RepositoryRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class ValueSerializer(serializers.Serializer):
    """`serialize_value`: `null` nos dois sem valor na janela da release."""

    value = nullable_number()
    created_at = serializers.DateTimeField(allow_null=True)


# entity-analysis/


class EntityAnalysisEntitySerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    metric_type = serializers.CharField(required=False, help_text="Só no nível metric.")


class EntityAnalysisReferenceSerializer(serializers.Serializer):
    """`goal` na característica; `min_threshold`/`max_threshold` na medida."""

    goal = number(required=False)
    min_threshold = number(required=False)
    max_threshold = number(required=False)


class EntityAnalysisChildSerializer(ValueSerializer):
    key = serializers.CharField()
    name = serializers.CharField()
    weight = nullable_number()


class EntityAnalysisRepositorySerializer(ValueSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    children = EntityAnalysisChildSerializer(many=True)


class EntityAnalysisSerializer(serializers.Serializer):
    release = ReleaseRefSerializer()
    level = serializers.ChoiceField(choices=LEVELS)
    entity = EntityAnalysisEntitySerializer()
    reference = EntityAnalysisReferenceSerializer(allow_null=True)
    repositories = EntityAnalysisRepositorySerializer(many=True)


class EntityCatalogItemSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()


class EntityCatalogSerializer(serializers.Serializer):
    characteristic = EntityCatalogItemSerializer(many=True)
    subcharacteristic = EntityCatalogItemSerializer(many=True)
    measure = EntityCatalogItemSerializer(many=True)
    metric = EntityCatalogItemSerializer(many=True)


# entity-analysis/matrix/


class MatrixPathItemSerializer(serializers.Serializer):
    level = serializers.CharField()
    key = serializers.CharField()
    name = serializers.CharField()
    weight = nullable_number()


class MatrixColumnSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    weight = nullable_number()
    path = MatrixPathItemSerializer(many=True)


class MatrixTsqmiSerializer(serializers.Serializer):
    value = nullable_number()
    previous_value = nullable_number()


class MatrixCellSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = nullable_number()
    previous_value = nullable_number()
    contribution = nullable_number()


class MatrixRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tsqmi = MatrixTsqmiSerializer()
    cells = MatrixCellSerializer(many=True)


class EntityMatrixSerializer(serializers.Serializer):
    release = ReleaseRefSerializer()
    previous_release = ReleaseRefSerializer(allow_null=True)
    level = serializers.ChoiceField(choices=MATRIX_LEVELS)
    columns = MatrixColumnSerializer(many=True)
    repositories = MatrixRowSerializer(many=True)


# analysis-distribution/


class DistributionPeriodSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    first = serializers.DateTimeField(allow_null=True)
    last = serializers.DateTimeField(allow_null=True)


class DistributionAnalysisSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    value = number()
    is_outlier = serializers.BooleanField()


class DistributionSummarySerializer(serializers.Serializer):
    """`summarize`: tudo `null` (e `count`/`outliers` 0) sem análises."""

    count = serializers.IntegerField()
    min = nullable_number()
    p10 = nullable_number()
    q1 = nullable_number()
    median = nullable_number()
    q3 = nullable_number()
    p90 = nullable_number()
    max = nullable_number()
    iqr = nullable_number()
    lower_limit = nullable_number()
    upper_limit = nullable_number()
    outliers = serializers.IntegerField()
    mean = nullable_number()
    skewness = nullable_number()
    std = nullable_number()
    variance = nullable_number()


class DistributionEntitySerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    level = serializers.ChoiceField(choices=DISTRIBUTION_LEVELS)
    metric_type = serializers.CharField(allow_null=True)
    analyses = DistributionAnalysisSerializer(many=True)
    summary = DistributionSummarySerializer()


class AnalysisDistributionSerializer(serializers.Serializer):
    release = ReleaseRefSerializer()
    repository = RepositoryRefSerializer()
    level = serializers.ChoiceField(choices=DISTRIBUTION_LEVELS)
    key = serializers.CharField()
    period = DistributionPeriodSerializer()
    entity = DistributionEntitySerializer()
    children = DistributionEntitySerializer(many=True)


# correlation/


class CorrelationEntitySerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    normal = serializers.BooleanField(allow_null=True)


class CorrelationReleaseValuesSerializer(serializers.Serializer):
    release = ReleaseRefSerializer()
    values = serializers.DictField(child=nullable_number(), help_text="Valor de cada entidade, pela chave.")
    used = serializers.BooleanField()


class CorrelationPairSerializer(serializers.Serializer):
    row = serializers.CharField()
    column = serializers.CharField()
    coefficient = nullable_number()
    p_value = nullable_number()
    significant = serializers.BooleanField()


class CorrelationSerializer(serializers.Serializer):
    repository = RepositoryRefSerializer()
    level = serializers.ChoiceField(choices=CORRELATION_LEVELS)
    entities = CorrelationEntitySerializer(many=True)
    releases = ReleaseRefSerializer(many=True)
    excluded_releases = serializers.IntegerField()
    release_values = CorrelationReleaseValuesSerializer(many=True)
    method = serializers.ChoiceField(choices=("pearson", "spearman"), allow_null=True)
    non_normal = serializers.IntegerField(allow_null=True)
    critical_value = nullable_number()
    pairs = CorrelationPairSerializer(many=True)
    reason = serializers.ChoiceField(choices=("insufficient_releases", "insufficient_entities"), allow_null=True)


# release-dashboard/


class ReleaseTotalsSerializer(serializers.Serializer):
    characteristics = serializers.IntegerField()
    subcharacteristics = serializers.IntegerField()
    measures = serializers.IntegerField()
    metrics = serializers.IntegerField()
    repositories = serializers.IntegerField()
    files = serializers.IntegerField()


class ReleaseSummarySerializer(serializers.Serializer):
    release = ReleaseRefSerializer()
    totals = ReleaseTotalsSerializer()


class ReleaseRepositoryTsqmiSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tsqmi = ValueSerializer()


class ReleaseRepositoriesTsqmiSerializer(serializers.Serializer):
    release = ReleaseRefSerializer()
    repositories = ReleaseRepositoryTsqmiSerializer(many=True)


# repositories-tsqmi-release-history/


class TsqmiHistoryPointSerializer(ValueSerializer):
    release_id = serializers.IntegerField()
    previous_value = nullable_number()
    variation = nullable_number()
    variation_percent = nullable_number()


class TsqmiHistoryRepositorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    history = TsqmiHistoryPointSerializer(many=True)


class TsqmiReleaseHistorySerializer(serializers.Serializer):
    releases = ReleaseRefSerializer(many=True)
    repositories = TsqmiHistoryRepositorySerializer(many=True)


# release/{id}/analysis_data/


class PlannedCharacteristicSerializer(serializers.Serializer):
    """`get_planned_values`: `name` é a chave da característica."""

    name = serializers.CharField()
    value = number()


class AccomplishedCharacteristicSerializer(PlannedCharacteristicSerializer):
    """`calculate_diff`: `diff` é `null` numa característica que não foi planejada."""

    diff = nullable_number()


class AccomplishedRepositorySerializer(serializers.Serializer):
    repository_name = serializers.CharField()
    characteristics = AccomplishedCharacteristicSerializer(many=True)
    norm_diff = nullable_number()


class ReleaseAnalysisDataSerializer(serializers.Serializer):
    release = ReleaseAllSerializer()
    planned = PlannedCharacteristicSerializer(many=True)
    accomplished = AccomplishedRepositorySerializer(many=True)
