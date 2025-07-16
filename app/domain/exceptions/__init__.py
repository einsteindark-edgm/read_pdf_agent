"""Domain exceptions."""
from .domain_exceptions import (
    DomainException,
    DocumentNotFoundError,
    InvalidDocumentError,
    ExtractionError,
    DocumentSizeExceededError,
    UnsupportedDocumentTypeError
)

__all__ = [
    "DomainException",
    "DocumentNotFoundError", 
    "InvalidDocumentError",
    "ExtractionError",
    "DocumentSizeExceededError",
    "UnsupportedDocumentTypeError"
]
