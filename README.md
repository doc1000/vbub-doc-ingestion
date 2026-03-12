```markdown
# vbub-doc-ingestion

Document ingestion service for the **VaultBubbles** platform.

This service accepts uploaded documents, validates them, extracts clean text, normalizes structure, and returns a **single canonical document payload** suitable for downstream semantic processing such as topic modeling, embeddings, search, and RAG.

The system is designed with a **single-ingestion-contract philosophy**:

> Normalize once. Consume everywhere.

All parsing, cleanup, and validation occur exactly once during ingestion. Downstream systems receive a stable `CanonicalDocument` payload and do not repeat file-type logic.

---

# Project Overview

## Purpose

`vbub-doc-ingestion` is a reusable Python package (and optional HTTP service) responsible for transforming uploaded documents into normalized, machine-readable text with structured metadata.

It serves as the **ingestion boundary** for the VaultBubbles ecosystem.

The package supports two usage modes:

1. **Import mode (primary)** — VaultBubbles imports the package directly and calls its orchestration functions in-process.
2. **Service mode (optional)** — A thin FastAPI adapter exposes the same ingestion pipeline as an HTTP API.

The package:

- receives uploaded files
- validates file type and metadata
- preserves the original binary
- extracts usable text
- normalizes document structure
- returns a canonical JSON document

This canonical document is then used downstream by VaultBubbles for:

- topic modeling
- embeddings
- semantic search
- document visualization
- note-taking
- retrieval augmented generation (RAG)

---

## Target Users

Indirect users:

- VaultBubbles platform users uploading documents
- Researchers and analysts organizing documents
- Knowledge workers attaching notes to documents

Direct users:

- The **VaultBubbles backend service**, which calls this ingestion API.

---

## Problem This Service Solves

Most document pipelines suffer from:

- repeated parsing logic
- inconsistent text extraction
- format-specific downstream logic
- bloated ingestion pipelines

This service solves that by introducing a **single canonical ingestion contract**.

All document complexity is handled once at ingestion time.

Downstream systems receive a **stable normalized document representation**.

---

# Core Features

## MVP Features

### File Upload Ingestion

API endpoint accepts a single file and client metadata.

Input includes:

- binary file
- filename
- client metadata
- optional tags
- optional local path hint

---

### File Validation

Validation includes:

- file size limits
- MIME detection
- extension normalization
- SHA256 hashing
- duplicate detection hooks

---

### Binary Preservation

Original file binary is preserved exactly as uploaded.

This ensures:

- reproducibility
- traceability
- ability to re-parse in the future

---

### Parser Routing

File type is detected and routed to exactly one parser.

Supported formats in V1:

- txt
- md
- pdf
- docx
- csv
- xlsx

**Phase 7 note:** The router also accepts text-like file aliases (e.g. `.bat`, `.jsx`, `.ps1`, `.yaml`, `.json`) and suffixless files when content-based detection confirms they are plain text. Unsupported binary formats such as `.xls` are rejected cleanly with a 422 error; `.xls` uploads should be converted to `.xlsx` before uploading.

---

### Text Extraction

Each file type uses a dedicated extractor adapter.

Example libraries:

- PyMuPDF (PDF)
- python-docx (DOCX)
- stdlib csv
- openpyxl (XLSX)

---

### Text Normalization

Normalization includes:

- Unicode normalization
- whitespace cleanup
- line break harmonization
- structure preservation

---

### Boilerplate Removal

Removes common noise such as:

- repeating headers/footers
- page numbers
- formatting artifacts

---

### Tabular Flattening

CSV/XLSX tables are flattened into readable text blocks.

Numeric-heavy rows can be suppressed when they contain little semantic value.

---

### Canonical Document Generation

Final step produces the **CanonicalDocument payload** returned to the caller.

This payload contains:

- metadata
- normalized text
- source hints
- parser metadata
- binary reference

---

## Future Features

Not part of V1:

- HTML ingestion
- OCR support
- Tika fallback parser
- PowerPoint ingestion
- entity extraction
- semantic enrichment
- NER
- background ingestion queues

These are intentionally deferred to keep the ingestion layer simple and deterministic.

---

# Success Criteria

The ingestion service is considered successful if:

1. Upload endpoint accepts files reliably under configured size limits.
2. CanonicalDocument is produced for supported formats.
3. Extraction produces useful semantic text for downstream modeling.
4. Binary preservation is guaranteed.
5. End-to-end ingestion latency remains below acceptable thresholds for document uploads.
6. Downstream systems never need to inspect file types directly.

---

# System Architecture

## Service Architecture

```

VaultBubbles Backend
│
│ Import (primary) or HTTP request (optional)
▼
vbub_doc_ingestion package
│
▼
CanonicalDocument

```

The ingestion package can be used as a direct import or as an HTTP service.

It does not provide a frontend.

---

## Backend Runtime

Python stack:

- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn
- pytest

---

## Binary Storage

Current strategy:

- local filesystem storage during development

Example location:

```

/data/ingestion/blobs/

```

Long-term storage may migrate to object storage.

The ingestion service itself does **not own permanent storage responsibilities**.

---

## Database

This repository does **not manage document persistence**.

VaultBubbles uses:

- Supabase PostgreSQL
- vector storage for embeddings

CanonicalDocument payloads are returned to the backend for storage.

---

## LLM Usage

LLMs are **not used inside the ingestion service**.

LLM workflows occur downstream for:

- embeddings
- topic modeling
- semantic retrieval
- summarization

Ingestion is strictly deterministic.

---

# Folder / File Structure

Recommended project layout:

```

vbub_doc_ingestion/
│
├── src/
│   └── vbub_doc_ingestion/         # Core package (no FastAPI dependency)
│       ├── __init__.py              # Public API: orchestrate_ingestion, ClientMeta, CanonicalDocument
│       ├── config.py
│       ├── domain/
│       │   ├── contracts.py         # CanonicalDocument and related models
│       │   ├── enums.py
│       │   └── schemas.py           # ClientMeta
│       ├── orchestration/
│       │   └── ingest_file.py       # orchestrate_ingestion() entrypoint
│       ├── services/
│       │   ├── file_validation_service.py
│       │   ├── parser_router.py
│       │   ├── tag_policy_service.py
│       │   ├── text_normalization_service.py
│       │   ├── boilerplate_cleanup_service.py
│       │   ├── content_classification_service.py
│       │   └── tabular_text_policy_service.py
│       ├── extractors/
│       │   ├── base.py
│       │   ├── text_extractor.py
│       │   ├── pdf_extractor.py
│       │   ├── docx_extractor.py
│       │   ├── csv_extractor.py
│       │   └── xlsx_extractor.py
│       └── storage/
│           └── blob_store.py
│
├── adapters/
│   └── fastapi_app/                 # Optional HTTP adapter (requires FastAPI)
│       ├── main.py
│       ├── routes_ingest.py
│       └── error_handlers.py
│
├── tests/
│   ├── fixtures/
│   └── ...
│
├── pyproject.toml
└── README.md

````

---

# Data Models

## CanonicalDocument

Example output payload:

```json
{
  "documentId": "doc_123",
  "displayName": "report.docx",
  "canonicalMime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "extension": "docx",

  "binaryRef": {
    "storageKey": "blob/abc123",
    "checksumSha256": "abc...",
    "sizeBytes": 182334
  },

  "sourceLocator": {
    "deviceLabel": "PersonalLaptop",
    "osLabel": "Windows 11",
    "localPathHint": "C:/documents/report.docx"
  },

  "extraction": {
    "parserName": "DocxExtractor",
    "parserVersion": "0.1.0",
    "title": "Quarterly Report",
    "cleanText": "normalized document text...",
    "warnings": []
  },

  "metadata": {
    "tags": ["research", "finance"],
    "createdAt": "2026-03-10T12:00:00Z"
  },

  "status": "ready_for_indexing"
}
````

---

# Application Logic Overview

High-level ingestion flow:

```
Upload request
    │
    ▼
UploadGateway
    │
    ▼
FileValidationService
    │
    ▼
BinaryStorageService
    │
    ▼
ParserRouter
    │
    ▼
Extractor
    │
    ▼
TextNormalizationService
    │
    ▼
BoilerplateCleanupService
    │
    ▼
CanonicalDocumentBuilder
    │
    ▼
CanonicalDocument JSON
```

The orchestration layer coordinates all components.

---

# API Endpoints

## POST /ingest/file

Upload a document.

### Request

Multipart form upload:

```
file: binary
clientMeta: JSON
```

Example metadata:

```json
{
  "originalFilename": "report.docx",
  "browserMime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "sizeBytes": 182334,
  "localPathHint": "C:/documents/report.docx",
  "deviceLabel": "PersonalLaptop",
  "userTags": ["finance", "analysis"]
}
```

---

### Response

```
200 OK
```

Returns:

```
CanonicalDocument
```

---

## GET /health

Simple health check.

---

# Environment Variables

Example `.env.local.example`

```
APP_ENV=development
LOG_LEVEL=info

MAX_UPLOAD_SIZE_MB=25

BINARY_STORAGE_PATH=./data/blobs

HASH_ALGORITHM=sha256

SERVICE_NAME=vbub-doc-ingestion
```

---

# Setup Instructions

## Install the package

```
pip install -e .
```

To include FastAPI adapter dependencies:

```
pip install -e ".[server]"
```

To include test dependencies:

```
pip install -e ".[dev]"
```

---

## Usage: Import mode (primary)

```python
from vbub_doc_ingestion import orchestrate_ingestion, ClientMeta

meta = ClientMeta(original_filename="report.pdf")
doc = orchestrate_ingestion(file_bytes, "report.pdf", meta)
```

---

## Usage: Service mode (optional)

```
pip install -e ".[server]"
uvicorn adapters.fastapi_app.main:app --reload
```

Server runs at:

```
http://localhost:8000
```

---

# Testing Requirements

Tests use **pytest**.

Run tests:

```
pytest
```

Tests should include:

### Unit Tests

* parser extractors
* validation logic
* cleanup services

### Integration Tests

* full ingestion pipeline

### Fixture Tests

Example fixtures:

```
tests/fixtures/
  sample.pdf
  sample.docx
  sample.csv
```

---

# Deployment

This service deploys within the **VaultBubbles Fly.io app**.

It runs as a **separate process group** from the main backend.

Example structure:

```
Fly App: vaultbubbles

process groups:

backend
ingestion
```

Benefits:

* independent scaling
* independent deployment
* failure isolation

---

# Future Enhancements

Planned improvements include:

* HTML ingestion
* Tika fallback parsing
* OCR for scanned documents
* PPTX support
* entity extraction
* ingestion batching
* ingestion queues

These are intentionally deferred until the core ingestion contract stabilizes.

---

# Cursor Development Notes

Cursor uses the following files as architectural guides:

* README.md
* ARCHITECTURE_RULES.md
* IMPLEMENTATION_PLAN.md
* ingest_architecture_map.html

Developers should:

* implement one phase at a time
* follow IMPLEMENTATION_PLAN.md
* avoid implementing future features early
* keep FastAPI routes thin
* keep business logic in services and orchestration

The ingestion service should remain:

* deterministic
* lightweight
* modular
* easy to audit

Avoid adding:

* heavy dependencies
* LLM logic
* background job systems
* complex storage responsibilities

If unsure, prefer **simple and explicit implementations**.

```
```
