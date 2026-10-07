from staticfiles import SUPPORTED_MEASURES

"""Catálogo das métricas de runtime exigidas pelo Core 1.5.4."""

RUNTIME_AVAILABLE_METRICS = [
    {
        "key": "endpoint_calls",
        "name": "Endpoint calls",
        "metric_type": "INT",
    },
    {
        "key": "mean_response_time",
        "name": "Mean response time",
        "metric_type": "FLOAT",
    },
    {
        "key": "cpu_usage",
        "name": "CPU usage",
        "metric_type": "FLOAT",
    },
    {
        "key": "memory_usage",
        "name": "Memory usage",
        "metric_type": "FLOAT",
    },
]


_RUNTIME_METRIC_KEYS = frozenset(
    metric["key"] for metric in RUNTIME_AVAILABLE_METRICS
)

RUNTIME_MEASURE_KEYS = frozenset(
    key
    for measure in SUPPORTED_MEASURES
    for key, definition in measure.items()
    if _RUNTIME_METRIC_KEYS.intersection(definition["metrics"])
)
