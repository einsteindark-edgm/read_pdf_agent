"""DTO for document lists."""
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DocumentListDTO:
    """Data Transfer Object for document lists.
    
    This DTO encapsulates a list of document filenames.
    """
    documents: List[str]
    total_count: int
    
    @classmethod
    def from_list(cls, documents: List[str]) -> "DocumentListDTO":
        """Create from a simple list of documents."""
        return cls(
            documents=documents,
            total_count=len(documents)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "documents": self.documents,
            "total_count": self.total_count
        }