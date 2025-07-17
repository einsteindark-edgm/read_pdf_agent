"""Agent card definition for A2A protocol."""
from a2a.types import AgentCard, AgentCapabilities, AgentSkill


def get_agent_card() -> AgentCard:
    """Get the agent card for invoice extraction agent.
    
    Returns:
        AgentCard with capabilities and skills
    """
    return AgentCard(
        name="Invoice Extraction Agent",
        description="Specialized AI agent for extracting structured data from invoice PDFs. "
                   "Provides detailed analysis and structured data extraction for invoices, "
                   "including vendor details, line items, totals, taxes, and payment terms.",
        url="http://localhost:8005/",
        version="2.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text", "application/json"],
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False
        ),
        skills=[
            AgentSkill(
                id="extract_invoice_data",
                name="Extract Invoice Data",
                description="Extract comprehensive structured data from invoice PDFs including "
                           "invoice number, dates, vendor/customer details, line items, and totals",
                tags=["invoice", "extraction", "vendor", "customer", "total", "pdf"],
                examples=[
                    "extract invoice data from invoice-2024.pdf",
                    "analyze the invoice in factura-001.pdf",
                    "get invoice details from billing-statement.pdf",
                    "what's the total amount in invoice.pdf?",
                    "extract vendor information from factura.pdf"
                ]
            ),
            AgentSkill(
                id="extract_line_items",
                name="Extract Line Items",
                description="Extract detailed line items from invoices including descriptions, "
                           "quantities, unit prices, and amounts",
                tags=["line items", "products", "services", "invoice", "details"],
                examples=[
                    "what products are in this invoice?",
                    "list all line items from invoice.pdf",
                    "extract service details from the invoice",
                    "what items were purchased in this invoice?"
                ]
            ),
            AgentSkill(
                id="extract_payment_info",
                name="Extract Payment Information",
                description="Extract payment terms, due dates, bank details, and payment methods "
                           "from invoice documents",
                tags=["payment", "due date", "terms", "bank", "invoice"],
                examples=[
                    "when is the payment due for this invoice?",
                    "what are the payment terms?",
                    "extract bank account details from invoice",
                    "how should this invoice be paid?"
                ]
            ),
            AgentSkill(
                id="calculate_totals",
                name="Calculate Invoice Totals",
                description="Extract and verify invoice totals including subtotal, taxes, "
                           "discounts, and final amount",
                tags=["total", "tax", "subtotal", "amount", "calculation"],
                examples=[
                    "what's the total amount including tax?",
                    "calculate the tax amount in this invoice",
                    "verify the invoice totals",
                    "what's the subtotal before taxes?"
                ]
            ),
            AgentSkill(
                id="list_available_invoices",
                name="List Available Invoices",
                description="Get a list of all invoice PDF files available for extraction",
                tags=["list", "available", "invoices", "pdfs"],
                examples=[
                    "list available invoices",
                    "what invoices can you process?",
                    "show me available invoice documents",
                    "which PDFs are available?"
                ]
            )
        ]
    )