"""LangChain setup - infrastructure service for agent creation."""
import os
import logging
from typing import List, Optional, Any

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor as LangChainAgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain_core.prompts import ChatPromptTemplate

from app.application.ports import AgentService, Tool, AgentExecutor
from .pydantic_parser import PydanticReActOutputParser

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LangChainSetup(AgentService):
    """Infrastructure service for LangChain configuration and setup."""
    
    def __init__(self):
        """Initialize LangChain configuration."""
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite-001")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.tools: Optional[List[BaseTool]] = None
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    def set_tools(self, tools: List[BaseTool]):
        """Set the tools available to the agent.
        
        Args:
            tools: List of LangChain tools to use
        """
        self.tools = tools
    
    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor.
        
        Returns:
            Configured AgentExecutor
        """
        logger.info(f"Creating agent with {len(self.tools) if self.tools else 0} tools")
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.0,
            max_output_tokens=2000,
            google_api_key=self.api_key,
            timeout=120,
            max_retries=2,
            top_p=0.95,
        )
        
        # Create prompt
        template = """You are a specialized invoice reading agent with expertise in extracting structured data from invoice PDF files.

CRITICAL RULES:
1. You MUST ALWAYS use the MCP tools to read PDF content - NEVER generate or guess data
2. You CANNOT provide any invoice information without first using the read_doc_contents tool
3. If asked about a PDF, you MUST:
   - First use list_available_pdfs to verify the file exists
   - Then use read_doc_contents to get the actual PDF content
   - Only then analyze and extract data from the ACTUAL content
4. Do NOT make up or guess file names, content, or any invoice data
5. WAIT for the Observation after each Action - do not generate it yourself
6. The Observation will be provided by the system after executing your Action
7. If you try to provide invoice data without using tools first, you are HALLUCINATING

INVOICE EXTRACTION EXPERTISE:
- Extract key invoice fields: invoice number, date, due date, vendor details, customer details, line items, amounts, taxes
- Identify payment terms, purchase order references, and shipping information
- Handle multiple invoice formats and layouts
- Calculate totals and verify mathematical accuracy when possible

MANDATORY WORKFLOW:
For ANY request about a PDF or invoice:
1. Use list_available_pdfs to see what files are available
2. Use read_doc_contents with the exact filename to read the PDF
3. Analyze the ACTUAL content from the tool's observation
4. Extract data ONLY from what you read in the observation

YOUR RESPONSE FORMAT:
When providing your Final Answer, you MUST:
1. Only provide information that comes from the tool observations
2. FIRST provide a detailed analysis in natural language explaining what you found
3. THEN include the extracted data in JSON format at the end
4. If you haven't used tools, say "I need to read the PDF first using the available tools"

Example Final Answer format (ONLY after reading actual PDF content):
"I've analyzed the invoice and found the following information:

This is an invoice from [Vendor Name from actual PDF] issued to [Customer Name from actual PDF] on [Date from actual PDF]. The invoice number is [Number from actual PDF] with a total amount of [Amount from actual PDF]. 

[Continue with detailed analysis based on ACTUAL PDF content]

Here's the structured data extracted from the invoice:

```json
{{
  "invoice_number": "actual value from PDF",
  "date": "actual value from PDF",
  "vendor": {{...actual data...}},
  "customer": {{...actual data...}},
  "items": [...actual items...],
  "total": "actual total from PDF"
}}
```"

You have access to the following tools:
{tools}

Use EXACTLY this format:

Thought: I need to think about what to do
Action: [tool name from the list above]
Action Input: [input for the tool]

Then STOP and WAIT. The system will provide:
Observation: [actual result from the tool]

Only after receiving the Observation, continue with:
Thought: Based on the observation...

NEVER generate the Observation yourself. Always wait for it.

REMEMBER:
- You MUST use tools for EVERY request about PDFs
- Start with list_available_pdfs if you're unsure about the filename
- Use read_doc_contents to read the actual PDF content
- Base your entire analysis on the tool observations
- If you haven't used tools yet, your first thought should be about which tool to use

Final Answer: [provide detailed analysis followed by JSON data ONLY from actual tool observations]

Question: {input}
Thought: {agent_scratchpad}"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create agent with Pydantic parser
        agent = (
            {
                "input": lambda x: x["input"],
                "tools": lambda x: "\n".join([f"{tool.name}: {tool.description}" for tool in (self.tools or [])]),
                "tool_names": lambda x: ", ".join([tool.name for tool in (self.tools or [])]),
                "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
            }
            | prompt
            | llm
            | PydanticReActOutputParser()
        )
        
        # Create executor
        agent_executor = LangChainAgentExecutor(
            agent=agent,
            tools=self.tools if self.tools else [],
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        # Wrap in our protocol-compliant executor
        return AgentExecutorAdapter(agent_executor)
    
    def get_tools(self) -> List[Tool]:
        """Get the list of available tools.
        
        Returns:
            List of tools available to the agent
        """
        return self.tools or []


class AgentExecutorAdapter:
    """Adapter to make LangChain AgentExecutor comply with our protocol."""
    
    def __init__(self, langchain_executor: LangChainAgentExecutor):
        self._executor = langchain_executor
    
    async def ainvoke(self, input: dict) -> dict:
        """Execute the agent with given input."""
        return await self._executor.ainvoke(input)