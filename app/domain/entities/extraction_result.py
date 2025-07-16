"""Extraction result entity."""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from app.domain.entities.document import DocumentType


@dataclass(frozen=True)
class ExtractionResult:
    """Result of document data extraction.
    
    This is a domain entity that represents the outcome of extracting
    structured data from a document.
    """
    document_type: DocumentType
    extracted_data: Dict[str, Any]
    confidence_score: float
    analysis: str
    filename: Optional[str] = None
    
    def __post_init__(self):
        """Validate extraction result."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        if not self.extracted_data:
            raise ValueError("Extraction result must contain data")
    
    def is_high_confidence(self) -> bool:
        """Business rule: Determine if extraction has high confidence."""
        return self.confidence_score >= 0.8
    
    def is_complete(self) -> bool:
        """Business rule: Check if extraction has all required fields."""
        # This is a simplified check - in reality, this would depend on document type
        required_fields = self._get_required_fields()
        return all(field in self.extracted_data for field in required_fields)
    
    def _get_required_fields(self) -> list:
        """Get required fields based on document type."""
        if self.document_type == DocumentType.BILL_OF_LADING:
            return ["shipper", "consignee", "port_of_loading", "port_of_discharge"]
        elif self.document_type == DocumentType.AIR_WAYBILL:
            return ["shipper", "consignee", "airport_of_departure", "airport_of_destination"]
        elif self.document_type == DocumentType.INVOICE:
            return ["invoice_number", "date", "total_amount"]
        else:
            return []
    
    def get_field_count(self) -> int:
        """Get number of extracted fields."""
        return len(self.extracted_data)