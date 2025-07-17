"""Application settings."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    """Application configuration settings."""
    # API Keys
    google_api_key: str
    
    # MCP Configuration
    mcp_pdf_server_dir: str
    mcp_pdf_server_command: str
    mcp_pdf_server_args: str
    mcp_pdf_transport: str
    
    # Model Configuration
    gemini_model: str
    
    # Server Configuration
    a2a_host: str
    a2a_port: int
    
    # Document Configuration
    max_pdf_size_kb: int
    pdf_dir: str
    
    @classmethod
    def from_environment(cls) -> "Settings":
        """Load settings from environment variables."""
        load_dotenv()
        
        return cls(
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            mcp_pdf_server_dir=os.getenv("MCP_PDF_SERVER_DIR", ""),
            mcp_pdf_server_command=os.getenv("MCP_PDF_SERVER_COMMAND", "uv"),
            mcp_pdf_server_args=os.getenv("MCP_PDF_SERVER_ARGS", "run python mcp_documents_server.py"),
            mcp_pdf_transport=os.getenv("MCP_PDF_TRANSPORT", "stdio"),
            gemini_model=os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash"),
            a2a_host=os.getenv("A2A_HOST", "0.0.0.0"),
            a2a_port=int(os.getenv("A2A_PORT", "8005")),
            max_pdf_size_kb=int(os.getenv("MAX_PDF_SIZE_KB", "7000")),
            pdf_dir=os.getenv("PDF_DIR", "./data/pdfs")
        )


# Global settings instance
settings = Settings.from_environment()