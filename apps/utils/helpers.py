# utils/api_response.py

from rest_framework.response import Response
from rest_framework import status

def success(data=None, message="Success", code=status.HTTP_200_OK , status=status.HTTP_200_OK):
    return Response({
        "status": status,
        "success": True,
        "message": message,
        "data": data
    }, status=code)

def error(message="Error", errors=None, code=status.HTTP_400_BAD_REQUEST, status=status.HTTP_400_BAD_REQUEST):
    return Response({
        "status": status,
        "success": False,
        "message": message,
        "errors": errors
    }, status=code)
