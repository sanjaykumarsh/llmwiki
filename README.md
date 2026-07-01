# LLMwiki

LLMwiki is a pattern for building compounding, persistent personal knowledge bases. Instead of using traditional RAG (Retrieval-Augmented Generation) which parses documents and answers queries from scratch every single time, LLMwiki uses an LLM agent to incrementally compile, cross-reference, and structure markdown files that compile knowledge over time.

This workspace contains a unified, zero-config local Python application featuring a **FastAPI backend** (orchestrating search indexing, text parsing, and Gemini API agent loops) and a **premium Cyberpunk/Obsidian-hybrid dark-mode frontend** (delivering split-screen reader panels, chat drawers, and interactive D3.js force-directed graphs).

---

## 📁 Workspace Folder Structure

```
llmwiki/
├── raw/                 # Immutable source files (PDFs, TXT, MD, HTML)
├── wiki/                # Compounding wiki markdown files (LLM-managed)
│   ├── index.md         # Table of contents catalog
│   └── log.md           # Append-only operation history
├── wiki_schema.md       # Target system schema rules for the LLM agent
├── server.py            # FastAPI server and static asset router
├── agent.py             # Agent workflows (Ingest, Query, Lint) and search
├── index.html           # Web UI layout template
├── styles.css           # Glassmorphism design and styles
├── app.js               # Frontend controller and D3 graph engine
├── test_wiki.py         # Unit tests checking core indexing and link linting
└── README.md            # This documentation file
```

---

## ✨ Key Features

1. **Obsidian-Compatible Wiki**: The folder layout, double-bracket internal linking (`[[page-name]]`), kebab-case lowercase file naming, and YAML metadata frontmatter conform fully to Obsidian standards.
2. **Interactive Visual Graph**: A dynamic 2D force-directed node graph representing the compiled wiki pages, their categories, and connections. Drag nodes to reshape, hover for details, and click any node to open it in the document reader.
3. **Agentic Ingestion**: Automatically compiles uploaded raw documents into source summaries and links them to updated or newly created concept/entity pages.
4. **Compounding Queries**: Queries the wiki by retrieving pages using a lightweight local TF-IDF search index. The agent answers questions with inline page citations, and drafts a new compounding wiki page of the analysis which can be saved to the wiki.
5. **Structural & Semantic Linting**: Programmatically scans for broken links, orphan pages, and formatting errors, and uses Gemini to spot contradictions and data gaps.
6. **Code Editor**: A built-in markdown code editor to manually edit or override wiki pages.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed. Install the required dependencies:
```bash
py -m pip install fastapi uvicorn google-generativeai python-multipart python-dotenv pypdf
```

### 2. Launching the App
Run the FastAPI server inside your workspace folder:
```bash
py server.py
```
The application will start, served at: **`http://127.0.0.1:8000`**

### 3. Quick Start Flow
1. Open `http://127.0.0.1:8000` in your browser.
2. Click the **Settings** gear icon (top-right) and enter your **Gemini API Key**. This will save it locally to a `.env` file in the workspace directory.
3. Select a model in the right drawer (defaults to **Gemini 1.5 Flash** for speed; you can select **Gemini 1.5 Pro** for complex reasoning).
4. Click **Add** in the *Raw Sources* panel (left side) and upload your document (PDF, TXT, MD).
5. Click the uploaded file in the list and click **Compile into Wiki**. The terminal logs will show the pages created and updated.
6. Switch to the **Interactive Graph** tab to explore your knowledge graph or type questions in the **Query** tab.

---

## 🛠️ Verification & Testing

We have built a unit test suite to verify internal operations. Run tests using:
```bash
py test_wiki.py
```
This tests:
- Raw text parsing.
- TF-IDF indexing and search ranking.
- Programmatic link extraction, broken link mapping, and orphan page detection.

---

## 🔗 Obsidian Integration
Because LLMwiki maintains Obsidian standards, you can open the parent workspace folder directly as a vault in Obsidian. The LLM agent acts as the developer and indexer, and Obsidian can serve as your viewer, letting you browse the graph, run manual edits, or export slide decks via Marp.
