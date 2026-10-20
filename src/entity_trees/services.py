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

    char_keys = [
        c["key"] for c in config.data.get("characteristics", []) if "key" in c
    ]
    subchar_keys = [
        s["key"]
        for c in config.data.get("characteristics", [])
        for s in c.get("subcharacteristics", [])
        if "key" in s
    ]
    measure_keys = [
        m["key"]
        for c in config.data.get("characteristics", [])
        for s in c.get("subcharacteristics", [])
        for m in s.get("measures", [])
        if "key" in m
    ]

    chars_by_key = {
        c.key: c
        for c in SupportedCharacteristic.objects.filter(key__in=char_keys)
    }
    subchars_by_key = {
        s.key: s
        for s in SupportedSubCharacteristic.objects.filter(key__in=subchar_keys)
    }
    measures_by_key = {
        m.key: m
        for m in SupportedMeasure.objects.filter(
            key__in=measure_keys,
        ).prefetch_related("metrics")
    }

    root: Dict[str, Any] = {
        "id": None,
        "type": "tsqmi",
        "key": "tsqmi",
        "name": "TSQMI",
        "description": TSQMI_ROOT_DESCRIPTION,
        "weight": 100,
        "children": [],
    }

    for char_dict in config.data.get("characteristics", []):
        char_key = char_dict.get("key")
        char_obj = chars_by_key.get(char_key)

        char_node: Dict[str, Any] = {
            "id": char_obj.id if char_obj else None,
            "type": "characteristic",
            "key": char_key,
            "name": char_obj.name if char_obj else char_key,
            "description": char_obj.description if char_obj else None,
            "weight": char_dict.get("weight"),
            "children": [],
        }

        for subchar_dict in char_dict.get("subcharacteristics", []):
            subchar_key = subchar_dict.get("key")
            subchar_obj = subchars_by_key.get(subchar_key)

            subchar_node: Dict[str, Any] = {
                "id": subchar_obj.id if subchar_obj else None,
                "type": "subcharacteristic",
                "key": subchar_key,
                "name": subchar_obj.name if subchar_obj else subchar_key,
                "description": subchar_obj.description if subchar_obj else None,
                "weight": subchar_dict.get("weight"),
                "children": [],
            }

            for measure_dict in subchar_dict.get("measures", []):
                measure_key = measure_dict.get("key")
                measure_obj = measures_by_key.get(measure_key)

                measure_node: Dict[str, Any] = {
                    "id": measure_obj.id if measure_obj else None,
                    "type": "measure",
                    "key": measure_key,
                    "name": measure_obj.name if measure_obj else measure_key,
                    "description": measure_obj.description if measure_obj else None,
                    "weight": measure_dict.get("weight"),
                    "min_threshold": measure_dict.get("min_threshold", None),
                    "max_threshold": measure_dict.get("max_threshold", None),
                    "children": [],
                }

                if measure_obj:
                    for metric in measure_obj.metrics.all():
                        metric_node = {
                            "id": metric.id,
                            "type": "metric",
                            "key": metric.key,
                            "name": metric.name,
                            "description": metric.description,
                            "weight": None,
                            "children": [],
                        }
                        measure_node["children"].append(metric_node)

                subchar_node["children"].append(measure_node)

            char_node["children"].append(subchar_node)

        root["children"].append(char_node)

    return [root]
