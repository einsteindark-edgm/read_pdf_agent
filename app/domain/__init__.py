"""Domain layer - Business entities and rules."""
from .entities import Document, DocumentType, ExtractionResult
from .exceptions import (
    DocumentNotFoundError,
    InvalidDocumentError,
    ExtractionError,
    DocumentSizeExceededError,
    UnsupportedDocumentTypeError
)

__all__ = [
    "Document",
    "DocumentType", 
    "ExtractionResult",
    "DocumentNotFoundError",
    "InvalidDocumentError",
    "ExtractionError",
    "DocumentSizeExceededError",
    "UnsupportedDocumentTypeError"
]
