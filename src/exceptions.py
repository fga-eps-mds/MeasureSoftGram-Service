class MeasureSoftGramServiceException(Exception):
    ''' Base MeasureSoftGram CLI Exception '''
    pass


class IdNotFoundedException(MeasureSoftGramServiceException):
    ''' Raised when an invalid ID is provided '''
    pass