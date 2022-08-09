class RandomMetricTypeException(Exception):
    pass


class GithubCollectorParamsException(Exception):
    pass


class MissingSupportedMetricException(Exception):
    pass


class EntityNotDefinedInPreConfiguration(Exception):
    pass


class MeasureNotDefinedInPreConfiguration(
    EntityNotDefinedInPreConfiguration,
):
    pass


class SubCharacteristicNotDefinedInPreConfiguration(
    EntityNotDefinedInPreConfiguration
):
    pass
