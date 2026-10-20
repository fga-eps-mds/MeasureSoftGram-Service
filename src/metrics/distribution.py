from datetime import timedelta
from statistics import fmean, pstdev, quantiles

from entity_trees.services import resolve_release_configuration
from metrics.models import CollectedMetric, SupportedMetric
from releases.service import filter_release_window

# As linhas de uma coleta têm created_at um pouco diferentes (cada CollectedMetric
# recebe o próprio timezone.now()). Mesma tolerância de
# SupportedMetric.get_latest_metric_values (metrics/models.py:113).
COLLECTION_TOLERANCE = timedelta(minutes=20)


def summarize(values):
    """
    Resumo estatístico dos valores de uma métrica entre os arquivos (CA3).

    Quartis pelo método `inclusive` (o `linear` do NumPy). O desvio padrão é
    populacional, porque os arquivos do repositório são a população inteira.
    """
    if not values:
        return None

    ordered = sorted(values)
    if len(ordered) == 1:
        # no Python 3.12, `quantiles` exige pelo menos dois valores
        q1 = median = q3 = ordered[0]
    else:
        q1, median, q3 = quantiles(ordered, n=4, method="inclusive")

    return {
        "count": len(ordered),
        "min": ordered[0],
        "q1": q1,
        "median": median,
        "q3": q3,
        "max": ordered[-1],
        "mean": fmean(ordered),
        "std_dev": pstdev(ordered),
    }


def _latest_value_by_path(queryset):
    values = {}
    for path, value in queryset.order_by("-created_at").values_list("path", "value"):
        values.setdefault(path, value)
    return values


def _latest_in_release_window(queryset, release):
    return filter_release_window(queryset, release).order_by("-created_at", "-id").first()


def get_repository_distribution(repository, metric_key, release):
    """
    Valores por arquivo de uma métrica na última coleta do repositório dentro
    da janela da release, de dia a dia (CA7). Arquivos com ncloc = 0 ficam fora, como em
    MathModelServices._resolve_metric_params_in_memory.
    """
    file_rows = CollectedMetric.objects.filter(repository=repository, qualifier="FIL", path__isnull=False)
    # âncora: a linha mais recente entre a métrica pedida e o ncloc, para que o ncloc
    # gravado logo depois da métrica (na mesma coleta) fique dentro da janela. Uma
    # consulta por métrica usa o índice (repository, metric, -created_at).
    latest_rows = [
        _latest_in_release_window(file_rows.filter(metric__key=key), release) for key in (metric_key, "ncloc")
    ]
    anchor = max((row for row in latest_rows if row is not None), key=lambda row: row.created_at, default=None)
    if anchor is None:
        return {"collected_at": None, "excluded_files": 0, "summary": None, "files": []}

    collection = filter_release_window(file_rows, release).filter(
        created_at__gte=anchor.created_at - COLLECTION_TOLERANCE,
        created_at__lte=anchor.created_at,
    )
    ncloc_by_path = _latest_value_by_path(collection.filter(metric__key="ncloc"))
    empty_paths = {path for path, ncloc in ncloc_by_path.items() if ncloc == 0}
    value_by_path = _latest_value_by_path(collection.filter(metric__key=metric_key))

    files = [
        {"path": path, "value": value}
        for path, value in sorted(value_by_path.items())
        if path not in empty_paths
    ]
    return {
        "collected_at": anchor.created_at,
        "excluded_files": len(value_by_path) - len(files),
        "summary": summarize([file["value"] for file in files]),
        "files": files,
    }


def get_metric_reference(product, release, metric_key):
    """
    Mínimo e máximo da medida que usa a métrica, na configuração vigente ao
    fim da release (CA4). None quando nenhuma medida da configuração usa a
    métrica com os dois thresholds.
    """
    config = resolve_release_configuration(product, release)
    if config is None:
        return None

    # relação reversa em vez de SupportedMeasure.objects.filter: o CacheManager
    # compara kwargs string como conjunto de letras
    measure_keys = set(SupportedMetric.objects.get(key=metric_key).related_measures.values_list("key", flat=True))

    for characteristic in config.data["characteristics"]:
        for subcharacteristic in characteristic["subcharacteristics"]:
            for measure in subcharacteristic["measures"]:
                if measure["key"] in measure_keys and "min_threshold" in measure and "max_threshold" in measure:
                    return {
                        "measure": measure["key"],
                        "min_threshold": measure["min_threshold"],
                        "max_threshold": measure["max_threshold"],
                    }
    return None
