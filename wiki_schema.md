# LLMwiki Schema & Guidelines

This document defines the schema, conventions, and operational instructions for maintaining the LLMwiki personal knowledge base. Both human editors and LLM agents must adhere to these standards to keep the wiki structured, interlinked, and fully compatible with Obsidian.

---

## 1. Directory Structure

```
llmwiki/
├── raw/                 # Immutable raw sources (PDFs, TXT, markdown clippers, images)
├── wiki/                # Compounding wiki pages (LLM-managed)
│   ├── index.md         # Content-oriented table of contents
│   └── log.md           # Chronological activity log
└── wiki_schema.md       # This schema & rules file (this document)
```

---

## 2. File & Page Naming Conventions

- **Filenames**: Must be lowercase with hyphens replacing spaces (kebab-case). E.g., `neural-networks.md`, `attention-mechanism.md`.
- **File Extensions**: Must end with `.md`.
- **Title**: The filename should correspond exactly to the concepts or entities. Avoid prefixes or suffixes unless categorized (e.g., use `attention-mechanism.md` instead of `concept-attention-mechanism.md`).

---

## 3. Obsidian Wiki-Link Standards

- **Internal Links**: Use standard Obsidian double-bracket wiki-links: `[[page-name]]`.
- **Display Text**: To use alternative text in a link, use the pipe syntax: `[[page-name|Display Text]]`.
- **Anchor Links**: Link to headings within pages if necessary: `[[page-name#heading-title]]`.
- **Autocompletable Links**: Always ensure that when referencing a topic or entity, the link points to the exact kebab-case filename of that topic (without the `.md` extension).

---

## 4. Page Structure & YAML Frontmatter

Every wiki page must begin with YAML frontmatter containing metadata for index queries (compatible with Obsidian's Dataview plugin).

### A. Source Summary Page Template
Created when a new raw document is ingested.

```markdown
---
type: source-summary
title: "Original Document Title"
raw_source: "filename.ext"
category: "research-paper | article | book-chapter | transcript"
tags: [tag1, tag2]
date_ingested: YYYY-MM-DD
last_updated: YYYY-MM-DD
---

# Summary: Original Document Title

**Quick Summary**: 1-2 sentence high-level summary of the source.

---

## Key Takeaways
- **Takeaway 1**: Bulleted summary of a core point.
- **Takeaway 2**: Bulleted summary of another core point.

## In-depth Synthesis
Detailed breakdown of the content, linking to [[concept-page-1]] and [[concept-page-2]].

## Extracted Entities & Concepts
- [[entity-1]]: Description of relation.
- [[concept-1]]: Description of relation.

## Metadata & References
- **Author(s)**: Author names if available
- **Publication Date**: Date of original publication
- **File Path**: `raw/filename.ext`
```

### B. Concept / Entity Page Template
Aggregates and synthesizes knowledge about a specific topic across multiple sources.

```markdown
---
type: concept
title: "Concept Name"
sources: ["source-filename1.ext", "source-filename2.ext"]
tags: [tag1, tag2]
last_updated: YYYY-MM-DD
---

# Concept Name

**Summary**: 1-2 sentence definition of the concept or entity.

---

## Explanation
Detailed explanation of the topic. Ensure every major claim references its source, e.g., (source: filename1.pdf).

## Sub-topics / Details
Elaborate on specific facets of the concept. Link to sub-concepts using [[sub-concept-name]].

## Compounding Insights & Contradictions
- **Insight**: Compile synthesis findings.
- **Contradictions / Nuances**: If source A claims X and source B claims Y, note it here:
  > *Contradiction*: Source A (`filename1.ext`) states that X is true, whereas Source B (`filename2.ext`) argues Y.

## Related Pages
- [[related-page-1]]
- [[related-page-2]]
```

---

## 5. Index & Logging Conventions

### A. `wiki/index.md` Structure
The index page is content-oriented. It lists all pages categorized logically. The agent must update this page on every ingest or page-creation action.

```markdown
# LLMwiki Index

*Compounding Knowledge Base*

---

## Sources
- [[original-document-title]] - One-line description of the source document.

## Concepts & Topics
- [[concept-name]] - One-line definition of the concept.

## Entities (People, Orgs, Projects)
- [[entity-name]] - One-line definition of the entity.
```

### B. `wiki/log.md` Structure
The log is chronological and append-only. Each entry must follow a parseable prefix syntax.

Format:
```markdown
# Activity Log

## [YYYY-MM-DD] ingest | Title of Source
- Added raw source `raw/filename.ext`
- Created summary page [[filename]]
- Updated [[concept-1]], [[concept-2]]
- Updated index page [[index]]

## [YYYY-MM-DD] query | Question text summary
- User asked: "..."
- Generated answer, saved to [[new-analysis-page]]

## [YYYY-MM-DD] lint | Weekly audit
- Checked for orphans and broken links.
- Fixed 2 broken links in [[concept-x]].
```

---

## 6. Citation & Conflict Rules

1. **Factual Claims**: Every factual claim in a concept/entity page must include a trailing reference indicating the source: `(source: source-filename.ext)`.
2. **Conflicting Claims**: Never override old data with new data if they contradict. Instead, document both viewpoints, note the conflict, and cite the respective sources.
3. **Unverified Claims**: If a concept is created or a claim is made without direct support from any raw document, it must be flagged with `(source: unverified)`.
