"""
Custom exception handlers for the API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response data
        custom_response_data = {
            'success': False,
            'error': {
                'message': None,
                'details': None
            }
        }

        # Handle different exception types
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                custom_response_data['error']['details'] = exc.detail
                # Get first error message as main message
                first_key = list(exc.detail.keys())[0]
                first_error = exc.detail[first_key]
                if isinstance(first_error, list):
                    custom_response_data['error']['message'] = first_error[0]
                else:
                    custom_response_data['error']['message'] = str(first_error)
            elif isinstance(exc.detail, list):
                custom_response_data['error']['message'] = exc.detail[0]
                custom_response_data['error']['details'] = exc.detail
            else:
                custom_response_data['error']['message'] = str(exc.detail)
        else:
            custom_response_data['error']['message'] = str(exc)

        response.data = custom_response_data

    return response
