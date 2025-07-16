"""Pydantic-based output parsers for LangChain agents."""
import re
import json
from typing import Union, Dict, Any
from pydantic import BaseModel, Field, field_validator

from langchain.agents.agent import AgentOutputParser
from langchain.schema.agent import AgentAction, AgentFinish


class ToolInput(BaseModel):
    """Base model for tool inputs with automatic conversion."""
    
    @classmethod
    def from_string(cls, value: str) -> Dict[str, Any]:
        """Convert a string value to the expected dictionary format.
        
        Override this method in subclasses for custom conversion logic.
        """
        # Default: wrap string in a generic 'input' field
        return {"input": value}


class MCPReadDocInput(ToolInput):
    """Input model for MCP read_doc_contents tool."""
    doc_id: str = Field(..., description="The document ID or filename to read")
    
    @classmethod
    def from_string(cls, value: str) -> Dict[str, Any]:
        """Convert a filename string to doc_id format."""
        # Remove quotes if present
        value = value.strip('"\'')
        return {"doc_id": value}


class NoParamsToolInput(ToolInput):
    """Input model for tools that take no parameters."""
    
    @classmethod
    def from_string(cls, value: str) -> Dict[str, Any]:
        """Tools with no params return empty dict."""
        return {}


class MCPToolInputs:
    """Registry of tool input models."""
    _registry: Dict[str, type[ToolInput]] = {
        "read_doc_contents": MCPReadDocInput,
        "list_available_pdfs": NoParamsToolInput,
        # Add more tools as needed
    }
    
    @classmethod
    def get_model(cls, tool_name: str) -> type[ToolInput]:
        """Get the input model for a tool, or default ToolInput."""
        return cls._registry.get(tool_name, ToolInput)
    
    @classmethod
    def convert_input(cls, tool_name: str, value: Union[str, Dict]) -> Dict[str, Any]:
        """Convert input to the correct format for a tool."""
        if isinstance(value, dict):
            # Already a dict, validate it with the model
            model_class = cls.get_model(tool_name)
            try:
                # Validate the dict structure
                instance = model_class(**value)
                return instance.model_dump()
            except Exception:
                # If validation fails, return as-is
                return value
        else:
            # String input, use the model's from_string method
            model_class = cls.get_model(tool_name)
            return model_class.from_string(str(value))


class PydanticReActOutputParser(AgentOutputParser):
    """Output parser that uses Pydantic models for type conversion."""
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse agent output with Pydantic-based type conversion."""
        # Check if this is a final answer
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text,
            )
        
        # Parse action and action input
        action_match = re.search(r"Action:\s*(\w+)", text, re.IGNORECASE)
        if not action_match:
            raise ValueError(f"Could not parse action from: {text}")
        
        action = action_match.group(1)
        
        # Try to find JSON action input first
        action_input_match = re.search(r"Action Input:\s*({.*?})", text, re.IGNORECASE | re.DOTALL)
        
        if action_input_match:
            try:
                # Parse JSON input
                action_input = json.loads(action_input_match.group(1))
            except json.JSONDecodeError:
                # JSON parsing failed, try simple string extraction
                action_input = self._extract_simple_input(text)
        else:
            # No JSON found, extract simple string
            action_input = self._extract_simple_input(text)
        
        # Convert input using Pydantic models
        converted_input = MCPToolInputs.convert_input(action, action_input)
        
        return AgentAction(tool=action, tool_input=converted_input, log=text)
    
    def _extract_simple_input(self, text: str) -> str:
        """Extract simple string input from action input line."""
        simple_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if simple_match:
            return simple_match.group(1).strip()
        else:
            raise ValueError(f"Could not parse action input from: {text}")