"""LangChain implementation of ExtractionAgent port."""
from typing import Dict, Any
from app.application.ports import ExtractionAgent, AgentService
from app.domain.entities import Document, ExtractionResult, DocumentType
from app.domain.exceptions import ExtractionError
import json


class LangChainExtractionAgent(ExtractionAgent):
    """LangChain-based implementation of ExtractionAgent.
    
    This adapter implements the ExtractionAgent port using LangChain
    and Gemini for document extraction and NLP processing.
    """
    
    def __init__(self, agent_service: AgentService, pdf_service=None):
        """Initialize with service interfaces.
        
        Args:
            agent_service: Agent service that implements AgentService port
            pdf_service: Deprecated - kept for compatibility but not used
        """
        self.agent_service = agent_service
        self.agent_executor = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the agent with MCP tools."""
        if self._initialized:
            return
        
        # Initialize agent service (which will initialize MCP and get tools)
        if hasattr(self.agent_service, 'initialize'):
            await self.agent_service.initialize()
        
        # Create agent executor
        self.agent_executor = self.agent_service.create_agent_executor()
        
        self._initialized = True
    
    async def extract(self, document: Document) -> ExtractionResult:
        """Extract structured data from a document using LangChain.
        
        Args:
            document: Document entity to extract data from
            
        Returns:
            ExtractionResult with structured data
            
        Raises:
            ExtractionError: If extraction fails
        """
        if not self._initialized:
            await self.initialize()
        
        # Create extraction prompt
        prompt = f"Extract structured data from the PDF file: {document.filename}"
        
        try:
            # Use agent to extract
            result = await self.agent_executor.ainvoke({"input": prompt})
            
            # Parse the response
            output = result.get("output", "")
            
            # Try to extract JSON data from response
            extraction_data = self._extract_json_from_response(output)
            
            # Determine document type
            doc_type = self._determine_document_type(extraction_data, output)
            
            # Create extraction result
            return ExtractionResult(
                document_type=doc_type,
                extracted_data=extraction_data,
                confidence_score=0.9,  # TODO: Calculate real confidence
                analysis=output,
                filename=document.filename
            )
            
        except Exception as e:
            raise ExtractionError(f"Extraction failed: {str(e)}")
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message using LangChain agent.
        
        Args:
            message: User's natural language request
            
        Returns:
            Response dictionary with results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Let the agent handle the request
            result = await self.agent_executor.ainvoke({"input": message})
            
            # Extract the output
            output = result.get("output", "")
            
            # Check if tools were used by looking at intermediate steps
            intermediate_steps = result.get("intermediate_steps", [])
            tools_used = len(intermediate_steps) > 0
            
            # If no tools were used and the request is about a PDF, return an error
            if not tools_used and any(keyword in message.lower() for keyword in ['pdf', 'invoice', 'extract', 'analyze', 'document']):
                return {
                    "success": False,
                    "message": "I need to use the available tools to read PDF files. Please ensure I have access to the MCP tools.",
                    "data": None
                }
            
            # Structure the response
            response = {
                "success": True,
                "message": output,
                "data": None
            }
            
            # Try to extract structured data if present
            if "{" in output and "}" in output:
                try:
                    json_data = self._extract_json_from_response(output)
                    if json_data:
                        response["data"] = json_data
                except:
                    pass  # If JSON extraction fails, keep raw output
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}",
                "data": None
            }
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON data from agent response."""
        import re
        
        # First try to find JSON in markdown code blocks
        code_block_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If not found in code blocks, try to find the last complete JSON object
        # This regex finds JSON objects more accurately
        json_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        json_candidates = list(json_matches)
        
        # Try from the last match (most likely to be the structured data)
        for match in reversed(json_candidates):
            try:
                json_str = match.group()
                # Basic validation that it looks like invoice data
                data = json.loads(json_str)
                if isinstance(data, dict) and any(key in str(data).lower() for key in ['invoice', 'vendor', 'customer', 'total', 'date']):
                    return data
            except json.JSONDecodeError:
                continue
        
        return {}
    
    def _determine_document_type(self, data: Dict[str, Any], text: str) -> DocumentType:
        """Determine document type from extracted data or text."""
        # Check in extracted data first
        doc_type_str = data.get("document_type", "").upper()
        
        # Check in text if not in data
        if not doc_type_str:
            text_upper = text.upper()
            if "BILL OF LADING" in text_upper or "B/L" in text_upper:
                doc_type_str = "BILL_OF_LADING"
            elif "AIR WAYBILL" in text_upper or "AWB" in text_upper:
                doc_type_str = "AIR_WAYBILL"
            elif "INVOICE" in text_upper:
                doc_type_str = "INVOICE"
        
        # Map to enum
        try:
            return DocumentType(doc_type_str.replace(" ", "_").replace("-", "_"))
        except:
            return DocumentType.UNKNOWN