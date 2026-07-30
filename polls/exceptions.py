from rest_framework.views import exception_handler

def custom_error_contract_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        original_data = response.data
        
        error_code = getattr(exc, 'default_code', 'invalid_request')

        response.data = {
            "error_code": error_code.upper(),
            "message": "The server could not process the request.",
            "details": original_data 
        }

    return response
