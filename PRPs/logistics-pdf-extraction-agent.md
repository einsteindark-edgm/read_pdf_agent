name: "Logistics PDF Extraction Agent with Chainlit UI"
description: |

## Purpose
Build a LangChain-powered PDF extraction agent exposed via Chainlit that processes logistics documents (B/L, AWB) using Gemini Flash 2.0, returning both structured data and analysis insights.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Build a complete async PDF extraction agent that:
- Loads PDFs from `data/pdfs/` directory
- Extracts text/tables using pdfplumber
- Processes with Gemini Flash 2.0 via LangChain
- Returns structured data (Pydantic) + free-text analysis
- Streams tokens via Chainlit UI
- Validates PDF size (75-350KB)
- Handles errors gracefully

## Why
- **Business value**: Automate manual logistics document processing
- **Integration**: Foundation for future document classification and DB storage
- **Problems solved**: Manual data entry errors, processing delays, unstructured document handling

## What
User uploads/selects a PDF in Chainlit, sees streaming analysis and structured data extraction in real-time.

### Success Criteria
- [ ] PDFs load from `data/pdfs/` directory
- [ ] Size validation rejects files >350KB  
- [ ] Gemini Flash 2.0 extracts structured fields
- [ ] Analysis provides bullet-point insights
- [ ] Tokens stream to Chainlit UI
- [ ] Errors display user-friendly messages

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://python.langchain.com/docs/how_to/structured_output/
  why: Shows PydanticOutputParser usage and format_instructions pattern
  
- file: examples/chainlit_langchain_app.py
  why: Exact pattern for Chainlit + LangChain async streaming
  
- file: examples/langchain_pydantic_parser.py
  why: Structured output with Pydantic models and JSON tags
  
- file: examples/pdfplumber_extract.py  
  why: Basic PDF text extraction pattern

- file: examples/langchain_google_genai_quickstart.py
  why: Gemini model initialization

- url: https://docs.chainlit.io/integrations/langchain
  why: Official integration guide for callbacks and streaming
  
- url: https://pypi.org/project/langchain-google-genai/
  why: ChatGoogleGenerativeAI configuration options

- docfile: CLAUDE.md
  why: Project conventions, async patterns, error handling
```

### Current Codebase tree
```bash
/Users/edgm/Documents/Projects/AI/read_pdf_agent/
├── PRPs/
│   └── templates/
│       └── prp_base.md
├── claude.md
├── examples/
│   ├── chainlit_langchain_app.py
│   ├── langchain_google_genai_quickstart.py
│   ├── langchain_pydantic_parser.py
│   └── pdfplumber_extract.py
└── feature_agent.md
```

### Desired Codebase tree with files to be added
```bash
/Users/edgm/Documents/Projects/AI/read_pdf_agent/
├── app/
│   ├── __init__.py          # Empty init file
│   ├── agent.py             # Main extraction agent logic
│   ├── chains.py            # LCEL chain definitions
│   └── prompts.py           # Extraction prompts
├── loaders/
│   ├── __init__.py          # Empty init file
│   └── pdf_loader.py        # Async PDF loading with validation
├── schemas/
│   ├── __init__.py          # Empty init file
│   └── extraction.py        # Pydantic models for output
├── data/
│   └── pdfs/                # Directory for PDF files
├── chainlit_app.py          # Chainlit UI entry point
├── .env.example             # Environment variables template
├── pyproject.toml           # Poetry dependencies
└── README.md                # Basic usage instructions
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: langchain-google-genai uses "models/gemini-2.0-flash" format
# Example: model = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-exp")

# CRITICAL: Chainlit requires storing runnable in user_session
# Example: cl.user_session.set("runnable", chain)

# CRITICAL: Use pydantic v2 for new code (not pydantic_v1 from examples)
# Example: from pydantic import BaseModel, Field, field_validator

# CRITICAL: PydanticOutputParser needs JSON tags in prompt
# Example: "Wrap the output in `json` tags"

# CRITICAL: Async all the way - no sync I/O in async functions
# Example: Use aiofiles for file operations if needed

# CRITICAL: pdfplumber is sync - wrap in asyncio.to_thread()
# Example: text = await asyncio.to_thread(extract_pdf_sync, path)
```

## Implementation Blueprint

### Data models and structure

```python
# schemas/extraction.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date

class LogisticsDocument(BaseModel):
    """Base extraction model for logistics PDFs"""
    document_type: str = Field(..., description="Type: BILL_OF_LADING, AIR_WAYBILL, or UNKNOWN")
    document_number: str = Field(..., description="B/L or AWB number")
    shipper: str = Field(..., description="Shipper/consignor name")
    consignee: str = Field(..., description="Consignee name")
    origin: str = Field(..., description="Port/airport of origin")
    destination: str = Field(..., description="Port/airport of destination")
    commodity_description: str = Field(..., description="Description of goods")
    weight: Optional[str] = Field(None, description="Total weight with unit")
    
    @field_validator('document_type')
    def validate_doc_type(cls, v):
        allowed = ["BILL_OF_LADING", "AIR_WAYBILL", "UNKNOWN"]
        if v.upper() not in allowed:
            return "UNKNOWN"
        return v.upper()

class ExtractionResult(BaseModel):
    """Complete extraction output"""
    data: LogisticsDocument
    analysis: str = Field(..., description="Free-text analysis with insights")
```

### List of tasks to be completed in order

```yaml
Task 1:
CREATE pyproject.toml:
  - Add all required dependencies
  - Use Python 3.11+
  - Include dev dependencies

Task 2:
CREATE .env.example:
  - Add all environment variables with descriptions
  - Include sensible defaults

Task 3:
CREATE directory structure:
  - Create all directories as shown in tree
  - Add __init__.py files

Task 4:
CREATE schemas/extraction.py:
  - Define Pydantic models
  - Add validators
  - Ensure JSON serializable

Task 5:
CREATE loaders/pdf_loader.py:
  - Implement async load_pdf function
  - Add size validation
  - Handle file errors gracefully

Task 6:
CREATE app/prompts.py:
  - Define extraction prompt template
  - Include format instructions
  - Add analysis requirements

Task 7:
CREATE app/chains.py:
  - Build LCEL chain
  - Configure Gemini model
  - Add output parser

Task 8:
CREATE app/agent.py:
  - Orchestrate PDF loading and extraction
  - Handle errors with specific messages
  - Return structured result

Task 9:
CREATE chainlit_app.py:
  - Implement Chainlit handlers
  - Add file selection UI
  - Stream tokens properly

Task 10:
CREATE README.md:
  - Basic setup instructions
  - Usage examples
  - Environment setup
```

### Per task pseudocode

```python
# Task 5: loaders/pdf_loader.py
import asyncio
from pathlib import Path
import pdfplumber
from typing import Optional

MAX_PDF_SIZE_KB = int(os.getenv("MAX_PDF_SIZE_KB", "350"))
PDF_DIR = Path(os.getenv("PDF_DIR", "./data/pdfs"))

async def load_pdf(name: str) -> str:
    """Load PDF and extract text asynchronously"""
    # PATTERN: Validate filename (no path traversal)
    if "/" in name or "\\" in name:
        raise ValueError("Invalid filename")
    
    # PATTERN: Check file exists
    pdf_path = PDF_DIR / name
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {name}")
    
    # PATTERN: Validate size
    size_kb = pdf_path.stat().st_size / 1024
    if size_kb > MAX_PDF_SIZE_KB:
        raise ValueError(f"PDF too large: {size_kb:.1f}KB > {MAX_PDF_SIZE_KB}KB")
    
    # PATTERN: Extract text in thread (pdfplumber is sync)
    def extract_sync():
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                if text := page.extract_text():
                    pages_text.append(text)
            return "\n\n".join(pages_text)
    
    return await asyncio.to_thread(extract_sync)

# Task 7: app/chains.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from schemas.extraction import ExtractionResult

def create_extraction_chain():
    """Create LCEL chain for PDF extraction"""
    # PATTERN: Initialize Gemini Flash 2.0
    model = ChatGoogleGenerativeAI(
        model="models/gemini-2.0-flash-exp",
        temperature=0.1,
        max_output_tokens=1000
    )
    
    # PATTERN: Setup parser
    parser = PydanticOutputParser(pydantic_object=ExtractionResult)
    
    # PATTERN: Build chain
    chain = prompt | model | parser
    return chain

# Task 9: chainlit_app.py
@cl.on_chat_start
async def on_chat_start():
    """Initialize session with PDF list"""
    # PATTERN: List available PDFs
    pdf_files = list((Path("data/pdfs")).glob("*.pdf"))
    
    # PATTERN: Create runnable
    from app.chains import create_extraction_chain
    chain = create_extraction_chain()
    cl.user_session.set("chain", chain)
    
    # PATTERN: Show file list
    files_list = "\n".join([f"- {f.name}" for f in pdf_files])
    await cl.Message(
        content=f"Available PDFs:\n{files_list}\n\nType a filename to extract:"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Process PDF extraction request"""
    chain = cl.user_session.get("chain")
    
    # PATTERN: Stream response
    msg = cl.Message(content="")
    
    try:
        # Load PDF
        pdf_text = await load_pdf(message.content.strip())
        
        # Extract with streaming
        async for chunk in chain.astream(
            {"pdf_text": pdf_text},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()])
        ):
            await msg.stream_token(chunk)
            
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()
    
    await msg.send()
```

### Integration Points
```yaml
ENVIRONMENT:
  - file: .env
  - vars:
    GOOGLE_API_KEY: "your-api-key"
    PDF_DIR: "./data/pdfs"
    MAX_PDF_SIZE_KB: "350"
    GEMINI_MODEL: "models/gemini-2.0-flash-exp"

DEPENDENCIES:
  - file: pyproject.toml
  - packages:
    langchain: "^0.3.0"
    langchain-google-genai: "^2.0.0"
    chainlit: "^1.0.0"
    pdfplumber: "^0.11.0"
    pydantic: "^2.0.0"
    python-dotenv: "^1.0.0"

STARTUP:
  - command: "chainlit run chainlit_app.py"
  - port: 8000
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# After creating each Python file:
ruff check app/ loaders/ schemas/ chainlit_app.py --fix
mypy app/ loaders/ schemas/ chainlit_app.py

# Expected: No errors. Common fixes:
# - Import errors: Add to __init__.py
# - Type errors: Add type hints
```

### Level 2: Unit Tests
```python
# test_pdf_loader.py
import pytest
from loaders.pdf_loader import load_pdf

@pytest.mark.asyncio
async def test_load_valid_pdf():
    """Test loading a valid PDF"""
    # Place test.pdf in data/pdfs/
    text = await load_pdf("test.pdf")
    assert len(text) > 0

@pytest.mark.asyncio  
async def test_file_not_found():
    """Test missing file raises error"""
    with pytest.raises(FileNotFoundError):
        await load_pdf("nonexistent.pdf")

@pytest.mark.asyncio
async def test_file_too_large(tmp_path):
    """Test size validation"""
    # Create large file
    large_file = tmp_path / "large.pdf"
    large_file.write_bytes(b"x" * 400 * 1024)
    
    with pytest.raises(ValueError, match="too large"):
        await load_pdf("large.pdf")

# test_extraction.py
from schemas.extraction import LogisticsDocument, ExtractionResult

def test_document_validation():
    """Test Pydantic validation"""
    doc = LogisticsDocument(
        document_type="bill_of_lading",
        document_number="BL123",
        shipper="ACME Corp",
        consignee="Customer Inc",
        origin="Shanghai",
        destination="Los Angeles",
        commodity_description="Electronics"
    )
    assert doc.document_type == "BILL_OF_LADING"  # Normalized

def test_extraction_result():
    """Test complete result model"""
    result = ExtractionResult(
        data=LogisticsDocument(...),
        analysis="Key insights:\n- High value shipment\n- Express delivery"
    )
    assert result.model_dump()  # JSON serializable
```

```bash
# Run tests:
pytest tests/ -v
```

### Level 3: Integration Test
```bash
# 1. Set environment variables
export GOOGLE_API_KEY="your-key"

# 2. Add sample PDF to data/pdfs/
cp examples/sample_bl.pdf data/pdfs/

# 3. Start Chainlit
chainlit run chainlit_app.py

# 4. In browser at http://localhost:8000
# - Type: sample_bl.pdf
# - Verify structured extraction appears
# - Check analysis bullets render

# Expected output format:
{
  "data": {
    "document_type": "BILL_OF_LADING",
    "document_number": "MAEU123456789",
    "shipper": "ACME CORPORATION",
    ...
  },
  "analysis": "Document Analysis:\n• International ocean freight shipment\n• Standard 20ft container\n• Port-to-port terms"
}
```

## Final Validation Checklist
- [ ] All directories created with __init__.py files
- [ ] Dependencies install: `poetry install`
- [ ] Environment configured: `.env` with GOOGLE_API_KEY
- [ ] Linting passes: `ruff check . --fix && mypy .`
- [ ] Sample PDF in data/pdfs/ directory
- [ ] Chainlit starts: `chainlit run chainlit_app.py`
- [ ] PDF extraction works with streaming
- [ ] Error cases show friendly messages
- [ ] Structured data validates against schema

---

## Anti-Patterns to Avoid
- ❌ Don't use sync file I/O in async functions
- ❌ Don't forget to wrap pdfplumber in asyncio.to_thread()
- ❌ Don't use pydantic_v1 - use pydantic v2
- ❌ Don't hardcode file paths - use env vars
- ❌ Don't skip size validation - PDFs can be huge
- ❌ Don't forget JSON tags in prompt for parser

## Confidence Score: 9/10

High confidence due to:
- Clear examples for every component
- Explicit patterns from working code
- Comprehensive error handling
- Step-by-step validation process

Minor uncertainty on exact Gemini Flash 2.0 model string (using best guess from docs).