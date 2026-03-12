# Decisions

## 2026-03-10 — Separate repo for ingestion
Reason:
- isolate complexity
- easier local testing
- cleaner integration contract

## 2026-03-10 — Same Fly app, separate process group
Reason:
- operational simplicity
- machine isolation
- pattern reusable for other app components



## 2026-03-12 — Package conversion: ingestion_service -> vbub_doc_ingestion
Reason:
- VaultBubbles needs to import ingestion directly, not just call via HTTP
- core pipeline must not depend on FastAPI
- enables dual mode: import (primary) and HTTP service (optional adapter)
- proper Python packaging with pyproject.toml and src layout
- ClientMeta moved from api/schemas to domain/schemas (breaks core-depends-on-API coupling)
- FastAPI code moved to adapters/fastapi_app/ as thin transport wrapper

---

## to do ideas

## excel junkiness
a lot of wierd characters... unnecessarily long. - only using extension to decide file type

## create a small fixed text pack to make sure that local and remote behave correctly - can be referenced by test set:
sample.txt
sample.md
sample.pdf
sample.docx
sample.csv
sample.xlsx
one unsupported file
one malformed metadata request

save payload examples to compare local vs remote

## test linux vs windows issues:
Because local dev was on Windows and deploy is Linux, the things most worth watching are:

file path handling

temp/binary storage directory permissions

MIME detection behavior

package/system dependency differences

newline/encoding corner cases

So yes, your testing plan is correct, but I’d add one explicit step:

6. Verify binary storage path and permissions remotely

Make sure the ingestion process can actually write to its configured local storage path in Fly.

A service can pass all local tests and still fail remotely if:

the directory doesn’t exist

the process user lacks permission

storage is ephemeral in a way you didn’t expect