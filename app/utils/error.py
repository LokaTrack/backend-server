from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

class ErrorResponse:
    """Standardized error response format"""
    def __init__(
        self, 
        status: str = "fail",
        message: str = "An error occurred",
        errors: Optional[List[Dict[str, Any]]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.status_code = status_code
        self.body = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if errors:
            self.body["errors"] = errors
    
    def to_response(self):
        return JSONResponse(
            status_code=self.status_code,
            content=self.body
        )

def format_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format validation errors from Pydantic into a standardized format"""
    formatted_errors = []
    for error in errors:
        formatted_error = {
            "field": ".".join([str(loc) for loc in error["loc"] if loc != "body" and loc != "query"]),
            "type": error["type"],
            "message": error["msg"],
            "input": error.get("input", None)
        }
        formatted_errors.append(formatted_error)
    return formatted_errors

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions from Pydantic"""
    errors = format_validation_errors(exc.errors())
    error_msg = "Validation error" if errors else "Invalid request"
    
    return ErrorResponse(
        status="fail",
        message=error_msg,
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    ).to_response()

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return ErrorResponse(
        status="fail",
        message=str(exc.detail) if isinstance(exc.detail, str) else exc.detail.get("message", "An error occurred"),
        errors=exc.detail.get("errors", None) if isinstance(exc.detail, dict) else None,
        status_code=exc.status_code
    ).to_response()

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return ErrorResponse(
        status="error",
        message=str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ).to_response()