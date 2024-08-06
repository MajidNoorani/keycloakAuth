from rest_framework.exceptions import APIException

class EampleException(APIException):
    status_code = 401
    default_detail = 'Authentication failed. Either the token is not valid or timed out.'
    default_code = 'unauthenticated'