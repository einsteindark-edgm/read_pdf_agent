"""Agent card definition for A2A protocol."""
from a2a.types import AgentCard, AgentCapabilities, AgentSkill


def get_agent_card() -> AgentCard:
    """Get the agent card for document extraction agent.
    
    Returns:
        AgentCard with capabilities and skills
    """
    return AgentCard(
        name="Document Extraction Agent",
        description="AI-powered agent that extracts structured data from PDFs in the static folder. "
                   "Automatically detects document types and provides detailed analysis.",
        url="http://localhost:8080/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text", "application/json"],
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False
        ),
        skills=[
            AgentSkill(
                id="extract-pdf",
                name="Extract PDF by Name",
                description="Extract structured data from a PDF file by providing its filename. "
                           "The PDF must exist in the data/pdfs folder.",
                tags=["pdf", "extraction", "document", "invoice", "bill-of-lading", "analysis"],
                examples=[
                    "extract invoice.pdf",
                    "analyze bill-of-lading-template.pdf", 
                    "what's in document-2024.pdf?",
                    "get data from customs-form.pdf",
                    "extract shipment.pdf"
                ]
            ),
            AgentSkill(
                id="list-pdfs",
                name="List Available PDFs",
                description="Get a list of all PDF files available for extraction",
                tags=["list", "available", "pdfs"],
                examples=[
                    "list available pdfs",
                    "what pdfs can you extract?",
                    "show me available documents"
                ]
            )
        ]
    )