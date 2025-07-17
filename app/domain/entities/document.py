"""Document entity - core business object."""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents the system can process."""
    BILL_OF_LADING = "BILL_OF_LADING"
    AIR_WAYBILL = "AIR_WAYBILL"
    INVOICE = "INVOICE"
    PACKING_LIST = "PACKING_LIST"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Document:
    """Core business entity representing a document.
    
    This is a domain entity - it contains business logic and rules
    but has no dependencies on external frameworks or infrastructure.
    """
    filename: str
    content: str
    document_type: Optional[DocumentType] = None
    
    def __post_init__(self):
        """Validate document on creation."""
        if not self.filename:
            raise ValueError("Document must have a filename")
        if not self.is_valid_pdf():
            raise ValueError(f"Document must be a PDF file: {self.filename}")
    
    def is_valid_pdf(self) -> bool:
        """Business rule: Document must be a PDF file."""
        return self.filename.lower().endswith('.pdf')
    
    def is_empty(self) -> bool:
        """Business rule: Check if document has no content."""
        return not self.content or not self.content.strip()
    
    def get_size_kb(self) -> float:
        """Calculate document size in KB."""
        if not self.content:
            return 0.0
        return len(self.content.encode('utf-8')) / 1024
    
    def exceeds_size_limit(self, max_size_kb: float = 7000.0) -> bool:
        """Business rule: Check if document exceeds size limit."""
        return self.get_size_kb() > max_size_kb