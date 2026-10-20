"""
Serviços para resolução e construção da árvore do modelo de qualidade.
"""

from typing import Any, Dict, List, Optional

from characteristics.models import SupportedCharacteristic
from measures.models import SupportedMeasure
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from subcharacteristics.models import SupportedSubCharacteristic

TSQMI_ROOT_DESCRIPTION = (
    "Total Software Quality Measurement Index: nota final do produto, "
    "agregada a partir das características e seus pesos."
)


def resolve_release_configuration(
    product,
    release: Optional[Release] = None,
) -> Optional[ReleaseConfiguration]:
    """
    Retorna a ReleaseConfiguration vigente para a release informada.
    Se release não for informada, retorna a configuração atual do produto.

    Regras:
    1. Se release fornecida: busca a configuração mais recente do produto
       com created_at <= release.end_at.
    2. Fallback: caso nenhuma configuração satisfaça created_at <= release.end_at,
       retorna a configuração mais antiga do produto.
    3. Se release não fornecida: retorna product.release_configuration.first()
       (a mais recente / vigente).
    """
    if release is not None:
        config = product.release_configuration.filter(
            created_at__lte=release.end_at,
        ).first()
        if not config:
            config = product.release_configuration.order_by("created_at").first()
        return config

    return product.release_configuration.first()


def build_quality_model_tree(
    config: Optional[ReleaseConfiguration],
) -> List[Dict[str, Any]]:
    """
    Constrói a árvore hierárquica do modelo de qualidade a partir de uma ReleaseConfiguration:
    TSQMI -> características -> subcaracterísticas -> medidas -> métricas.

    Se config for None ou não contiver dados, retorna uma lista vazia ([]).
    """
    if not config or not config.data or "characteristics" not in config.data:
        return []

    characteristics = config.data.get("characteristics", [])
    subcharacteristics = [s for c in characteristics for s in c.get("subcharacteristics", [])]
    measures = [m for s in subcharacteristics for m in s.get("measures", [])]

    supported = {
        "characteristic": _by_key(SupportedCharacteristic.objects, characteristics),
        "subcharacteristic": _by_key(SupportedSubCharacteristic.objects, subcharacteristics),
        "measure": _by_key(SupportedMeasure.objects.prefetch_related("metrics"), measures),
    }

    root: Dict[str, Any] = {
        "id": None,
        "type": "tsqmi",
        "key": "tsqmi",
        "name": "TSQMI",
        "description": TSQMI_ROOT_DESCRIPTION,
        "weight": 100,
        "children": [_characteristic_node(char_dict, supported) for char_dict in characteristics],
    }

    return [root]


def _by_key(queryset, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Entidades suportadas das chaves da configuração, indexadas pela chave."""
    keys = [item["key"] for item in items if "key" in item]
    return {entity.key: entity for entity in queryset.filter(key__in=keys)}


def _entity_node(node_type: str, key, entity, weight, children: List[Dict[str, Any]], **extra) -> Dict[str, Any]:
    """Nó da árvore; sem a entidade suportada no banco, usa a chave como nome."""
    return {
        "id": entity.id if entity else None,
        "type": node_type,
        "key": key,
        "name": entity.name if entity else key,
        "description": entity.description if entity else None,
        "weight": weight,
        **extra,
        "children": children,
    }


def _characteristic_node(char_dict: Dict[str, Any], supported: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    key = char_dict.get("key")
    children = [_subcharacteristic_node(sub, supported) for sub in char_dict.get("subcharacteristics", [])]
    return _entity_node("characteristic", key, supported["characteristic"].get(key), char_dict.get("weight"), children)


def _subcharacteristic_node(subchar_dict: Dict[str, Any], supported: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    key = subchar_dict.get("key")
    children = [_measure_node(measure, supported) for measure in subchar_dict.get("measures", [])]
    return _entity_node(
        "subcharacteristic", key, supported["subcharacteristic"].get(key), subchar_dict.get("weight"), children
    )


def _measure_node(measure_dict: Dict[str, Any], supported: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    key = measure_dict.get("key")
    measure = supported["measure"].get(key)
    children = [_metric_node(metric) for metric in measure.metrics.all()] if measure else []
    return _entity_node(
        "measure",
        key,
        measure,
        measure_dict.get("weight"),
        children,
        min_threshold=measure_dict.get("min_threshold", None),
        max_threshold=measure_dict.get("max_threshold", None),
    )


def _metric_node(metric) -> Dict[str, Any]:
    return _entity_node("metric", metric.key, metric, None, [])
