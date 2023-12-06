class RandomMetricTypeException(Exception):
    pass


class GithubCollectorParamsException(Exception):
    pass


class MissingSupportedMetricException(Exception):
    pass


class MissingSupportedMeasureException(Exception):
    pass


class MissingSupportedSubCharacteristicError(Exception):
    pass


class EntityNotDefinedInPreConfiguration(ValueError):
    """
    Exceção criada quando uma entidade é procurada em uma pré-configuração,
    mas esta entidade não foi selecionada na pré-configuração.
    """

    pass


class MeasureNotDefinedInPreConfiguration(
    EntityNotDefinedInPreConfiguration,
):
    pass


class SubCharacteristicNotDefinedInPreConfiguration(
    EntityNotDefinedInPreConfiguration
):
    pass


class CharacteristicNotDefinedInPreConfiguration(
    EntityNotDefinedInPreConfiguration
):
    pass


class InvalidPreConfigException(ValueError):
    pass
