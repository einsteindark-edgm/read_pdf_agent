## FEATURE:
Create a LangChain-powered **Logistics PDF Extraction Agent** exposed via **Chainlit**.  
The agent must:

1. **Load one PDF at a time** from a configurable static directory (e.g. `./pdfs/`).
2. Extract raw text/tables locally (pdfplumber/PyPDF2) before LLM processing.
3. Call **Gemini Flash 2.0** via `ChatGoogleGenerativeAI`.
4. Return:
   - `data` – structured output validated against a Pydantic model (JSON-serializable).
   - `analysis` – free-text summary *and* bullet-point insights about the document.
5. Enforce a soft size guardrail (`MAX_PDF_SIZE_KB≈75–350`, based on real B/L & AWB samples:contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}).
6. Be fully async and stream tokens to Chainlit.

## EXAMPLES:
- `examples/pdfplumber_extract.py` – minimal PDF text extraction with **pdfplumber**.  
- `examples/langchain_google_genai_quickstart.py` – Gemini Flash invocation via **langchain-google-genai**.  
- `examples/langchain_pydantic_parser.py` – schema definition & parsing using **PydanticOutputParser**.  
- `examples/chainlit_langchain_app.py` – wiring a LangChain runnable into **Chainlit** UI.

## DOCUMENTATION:
- https://python.langchain.com/docs/how_to/structured_output/ – structured outputs with Pydantic.  
- https://docs.chainlit.io/integrations/langchain – official Chainlit × LangChain guide.  
- https://pypi.org/project/langchain-google-genai/ – quick-start for Gemini models in LangChain.

## OTHER CONSIDERATIONS:
- **Directory convention**: place PDFs in `data/pdfs/`; module `loaders/pdf_loader.py` exposes `async load_pdf(name:str)`.
- **Performance**: stream Gemini tokens to reduce latency; set `max_output_tokens` defensively (≤1 000).
- **Security**: validate file name against whitelist; reject files >`MAX_PDF_SIZE_KB`.
- **Async I/O**: all DB and LLM calls should be `async` to match Chainlit’s event loop.
- **Error handling**: raise `OutputParserException` on schema mismatch; surface nicely in Chainlit UI.
- **Config**: environment vars `GOOGLE_API_KEY`, `PDF_DIR`, `MAX_PDF_SIZE_KB`, `GEMINI_MODEL=models/gemini-2.0-flash`.

> **Folder structure note:**  
> See the **“Code structure & modularity”** section in `CLAUDE.md` for directory layout of this feature.
