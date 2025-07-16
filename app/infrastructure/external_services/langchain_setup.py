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
        self.model_name = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash")
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
        template = """You are an intelligent document processing agent with access to MCP tools for working with PDF files.

CRITICAL RULES:
1. You MUST use the tools provided to interact with PDFs
2. Do NOT make up or guess file names or content
3. WAIT for the Observation after each Action - do not generate it yourself
4. The Observation will be provided by the system after executing your Action

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

Final Answer: [your final response based on actual observations]

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