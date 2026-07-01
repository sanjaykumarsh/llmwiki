import os
import re
import json
import datetime
from pathlib import Path
import google.generativeai as genai

# Setup Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-flash-lite-latest"

def get_client():
    """Returns the genai model config."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=key)
    return genai

def extract_text(file_path: Path) -> str:
    """Extracts text content from various file types."""
    suffix = file_path.suffix.lower()
    if suffix in [".txt", ".md", ".markdown", ".html", ".htm", ".json", ".xml", ".csv"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or "")
            return "\n\n".join(text)
        except ImportError:
            return f"[Error: pypdf not installed. Cannot parse PDF file {file_path.name}. Please install pypdf via 'pip install pypdf'.]"
        except Exception as e:
            return f"[Error parsing PDF file {file_path.name}: {str(e)}]"
    else:
        # Fallback
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"[Unsupported binary file format: {file_path.name}]"

def build_search_index(wiki_dir: Path):
    """Builds a simple local search index of TF-IDF scores for all markdown files."""
    index = {}
    wiki_files = list(wiki_dir.glob("*.md")) + list(wiki_dir.glob("**/*.md"))
    
    # Exclude log.md and index.md from search context if desired, or keep them.
    # We will exclude log.md and index.md from core concept search.
    files_to_index = [f for f in wiki_files if f.name not in ["log.md", "index.md"]]
    
    doc_words = {}
    all_words = set()
    
    for file_path in files_to_index:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
            # Clean non-alphanumeric
            words = re.findall(r'[a-z0-9\-]+', content)
            doc_words[file_path] = words
            for w in words:
                all_words.add(w)
        except Exception:
            continue
            
    # Simple Term Frequency index
    # Returns word to list of (file, freq)
    for file_path, words in doc_words.items():
        word_counts = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1
        
        # Normalize
        total = len(words) or 1
        for w, count in word_counts.items():
            if w not in index:
                index[w] = []
            index[w].append((str(file_path.relative_to(wiki_dir)), count / total))
            
    return index

def search_wiki(query: str, wiki_dir: Path, top_n=5):
    """Searches the wiki using a simple TF-IDF scoring algorithm on the index."""
    query_words = re.findall(r'[a-z0-9\-]+', query.lower())
    if not query_words:
        # Return all pages up to top_n
        files = [f.relative_to(wiki_dir) for f in wiki_dir.glob("*.md") if f.name not in ["log.md", "index.md"]]
        return [str(f) for f in files[:top_n]]
        
    index = build_search_index(wiki_dir)
    scores = {}
    
    for word in query_words:
        if word in index:
            # Simple weighting: match score = TF * IDF
            # IDF = log(N / docs_with_word)
            n_docs = len(list(wiki_dir.glob("*.md"))) or 1
            idf = 1.0 + (n_docs / (len(index[word]) + 1))
            for file_rel, tf in index[word]:
                scores[file_rel] = scores.get(file_rel, 0.0) + (tf * idf)
                
    sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = [file_rel for file_rel, score in sorted_files[:top_n]]
    
    # Fallback to direct substring match in filenames if TF-IDF yields nothing
    if not results:
        for f in wiki_dir.glob("*.md"):
            if f.name in ["log.md", "index.md"]:
                continue
            name_lower = f.name.lower()
            if any(qw in name_lower for qw in query_words):
                results.append(str(f.relative_to(wiki_dir)))
                if len(results) >= top_n:
                    break
                    
    # Ultimate fallback: list first few pages
    if not results:
        files = [f.relative_to(wiki_dir) for f in wiki_dir.glob("*.md") if f.name not in ["log.md", "index.md"]]
        results = [str(f) for f in files[:top_n]]
        
    return results

def run_ingest(source_filename: str, raw_dir: Path, wiki_dir: Path, schema_path: Path, model_name=DEFAULT_MODEL) -> dict:
    """Ingests a new raw source file into the wiki using Gemini."""
    source_path = raw_dir / source_filename
    if not source_path.exists():
        raise FileNotFoundError(f"Source file {source_filename} not found in raw directory.")
        
    # 1. Read schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
        
    # 2. Read existing index for context
    index_path = wiki_dir / "index.md"
    index_content = ""
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()
            
    # 3. Read source text
    source_text = extract_text(source_path)
    
    # Truncate source text if too large (e.g. limit to ~60k chars for fast processing)
    # Gemini has a large context window, but this keeps API calls fast and cheap
    if len(source_text) > 120000:
        source_text = source_text[:120000] + "\n\n... [Source text truncated for context window size] ..."

    # 4. Read list of existing pages in the wiki to see what we can update
    existing_wiki_files = [f.name for f in wiki_dir.glob("*.md") if f.name not in ["log.md", "index.md"]]
    
    # Constructing prompt
    prompt = f"""
You are the LLMwiki Programmer. Your job is to ingest a new raw source document into the wiki, obeying the following schema rules:

<WIKI_SCHEMA>
{schema_content}
</WIKI_SCHEMA>

The user has added a new raw source: `{source_filename}`.
Existing wiki pages: {json.dumps(existing_wiki_files)}

Here is the table of contents (`wiki/index.md`) for context:
<WIKI_INDEX>
{index_content}
</WIKI_INDEX>

Here is the full text of the raw source `{source_filename}`:
<RAW_SOURCE_TEXT>
{source_text}
</RAW_SOURCE_TEXT>

Tasks:
1. Generate a "source-summary" page for this file. Name it based on the document title (kebab-case, e.g., `document-title.md`).
2. Identify which concepts or entities are discussed. For each:
   - Decide whether to CREATE a new concept/entity page (if it doesn't exist) or UPDATE an existing page (if it exists in the list above).
   - Draw information from this new source and synthesize it. Integrate the data. Cite using `(source: {source_filename})`.
   - Maintain Obsidian format (brackets `[[concept-link]]`, lowercase-hyphen names, etc.).
3. Formulate updates for `wiki/index.md` (add the source and new concepts).
4. Create an activity log entry for `wiki/log.md`.

You MUST output your response in JSON format matching this schema:
{{
  "summary_page": {{
    "filename": "summary-filename.md",
    "title": "Title of the source",
    "content": "Full Markdown content for the source summary page complying with the schema."
  }},
  "concept_updates": [
    {{
      "filename": "concept-filename.md",
      "action": "create" or "update",
      "title": "Concept Title",
      "content": "Full markdown content of the concept page. If action is 'update', you must provide the ENTIRE updated content of the file, merging old information (if any existed, but since you don't have its full contents, write a comprehensive synthesis including the new source and linking existing terms)."
    }}
  ],
  "log_entry": "## [{datetime.date.today().isoformat()}] ingest | Title of Source\\n- ...",
  "index_updates": {{
    "sources_addition": "- [[summary-filename]] - One-line description of the source.",
    "concepts_addition": [
      "- [[concept-filename]] - One-line description of the concept (only for NEWLY created concepts)."
    ]
  }}
}}

Be extremely thorough. Cite correctly. Make sure filenames are lowercase, kebab-case, and end with `.md`.
Do not include any wrapper other than the JSON block.
"""
    
    # Configure Gemini API
    client = get_client()
    model = client.GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    
    # Apply changes atomically
    modified_files = []
    
    # A. Write summary page
    sum_page = result["summary_page"]
    sum_path = wiki_dir / sum_page["filename"]
    with open(sum_path, "w", encoding="utf-8") as f:
        f.write(sum_page["content"].strip() + "\n")
    modified_files.append({"filename": sum_page["filename"], "action": "created", "type": "summary"})
    
    # B. Write/Update concept pages
    for concept in result.get("concept_updates", []):
        filename = concept["filename"]
        c_path = wiki_dir / filename
        
        # Read old content if updating to prevent losing manual/existing info
        # (Though LLM should provide the merged content, let's verify if we need to do merging or trust the LLM.
        # Typically the LLM does a complete synthesis. Let's write the LLM content.)
        action = "updated" if c_path.exists() else "created"
        
        # If the file already exists, let's double check if we want to merge it.
        # For simplicity and robust synthesis, the prompt instructs the LLM to output the FULL content.
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(concept["content"].strip() + "\n")
        modified_files.append({"filename": filename, "action": action, "type": "concept"})
        
    # C. Update index.md
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            idx_lines = f.readlines()
    else:
        idx_lines = ["# LLMwiki Index\n\n*Compounding Knowledge Base*\n\n---\n\n## Sources\n\n## Concepts & Topics\n\n## Entities (People, Orgs, Projects)\n"]
        
    new_idx_lines = []
    in_sources = False
    in_concepts = False
    
    source_added = False
    
    for line in idx_lines:
        new_idx_lines.append(line)
        if "## Sources" in line:
            in_sources = True
            in_concepts = False
        elif "## Concepts" in line or "## Entities" in line:
            if in_sources and not source_added:
                # Add source line
                new_idx_lines.insert(len(new_idx_lines)-1, result["index_updates"]["sources_addition"] + "\n")
                source_added = True
            in_sources = False
            if "## Concepts" in line:
                in_concepts = True
            else:
                in_concepts = False
        elif in_concepts:
            # We will insert new concepts right below ## Concepts & Topics header if it's currently empty
            # Or we can append them at the end of concepts section.
            pass
            
    # Simple search & insert for sources
    idx_content = "".join(new_idx_lines)
    
    # Insert source
    source_add = result["index_updates"]["sources_addition"]
    # Check if already in index
    link_search = f"[[{sum_page['filename'].replace('.md', '')}]]"
    if link_search not in idx_content:
        # Insert after ## Sources header
        header_pos = idx_content.find("## Sources")
        if header_pos != -1:
            newline_pos = idx_content.find("\n", header_pos)
            # Check if there is a "*No sources ingested yet.*" placeholder
            placeholder = "*No sources ingested yet.*"
            if placeholder in idx_content:
                idx_content = idx_content.replace(placeholder, "")
            idx_content = idx_content[:newline_pos+1] + source_add + "\n" + idx_content[newline_pos+1:]
            
    # Insert concepts
    for concept_add in result["index_updates"].get("concepts_addition", []):
        concept_link = concept_add.split(" - ")[0].strip() # E.g., [[concept-name]]
        if concept_link not in idx_content:
            # Try to place under ## Concepts & Topics
            header_pos = idx_content.find("## Concepts & Topics")
            if header_pos != -1:
                newline_pos = idx_content.find("\n", header_pos)
                placeholder = "*No concepts created yet.*"
                if placeholder in idx_content:
                    idx_content = idx_content.replace(placeholder, "")
                idx_content = idx_content[:newline_pos+1] + concept_add + "\n" + idx_content[newline_pos+1:]
                
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(idx_content)
    modified_files.append({"filename": "index.md", "action": "updated", "type": "index"})
    
    # D. Append to log.md
    log_path = wiki_dir / "log.md"
    log_entry = result["log_entry"].strip()
    
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
    else:
        log_content = "# Activity Log\n\n*Log of all operations performed on LLMwiki (ingests, queries, lints).*\n\n---\n"
        
    # Append after --- header divider or insert at top of log entries (below header)
    divider_pos = log_content.find("---")
    if divider_pos != -1:
        insert_pos = divider_pos + 3
        log_content = log_content[:insert_pos] + "\n\n" + log_entry + log_content[insert_pos:]
    else:
        log_content += "\n\n" + log_entry
        
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_content)
    modified_files.append({"filename": "log.md", "action": "updated", "type": "log"})
    
    return {
        "summary": sum_page["title"],
        "filename": sum_page["filename"],
        "modified_files": modified_files,
        "raw_source": source_filename
    }

def run_query(question: str, wiki_dir: Path, schema_path: Path, model_name=DEFAULT_MODEL) -> dict:
    """Queries the wiki by searching relevant files and utilizing Gemini to formulate an answer."""
    # 1. Read schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
        
    # 2. Search relevant wiki pages
    relevant_files = search_wiki(question, wiki_dir, top_n=6)
    
    # 3. Read content of relevant files
    context_pages = []
    for rel_file in relevant_files:
        filepath = wiki_dir / rel_file
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                context_pages.append(f"### Page: {rel_file}\n\n{f.read()}")
                
    context_str = "\n\n---\n\n".join(context_pages) if context_pages else "*No relevant wiki pages found.*"
    
    prompt = f"""
You are the LLMwiki Assistant. Your job is to answer a user's question about the knowledge base using the retrieved pages as context.
You must cite the source pages using Obsidian double-bracket wiki-links like `[[page-name]]` or citations like `(source: filename.ext)`.

Here are the schema rules:
<WIKI_SCHEMA>
{schema_content}
</WIKI_SCHEMA>

Here is the retrieved wiki context:
<WIKI_CONTEXT>
{context_str}
</WIKI_CONTEXT>

User Question: "{question}"

Instructions:
1. Synthesize a detailed, accurate answer strictly based on the context. If the context does not contain the answer, state so clearly, but answer as much as you can.
2. Provide citations for all key assertions.
3. Suggest if this answer is valuable enough to be saved as a new page in the wiki (e.g. as a summary analysis).
   - If YES, output the proposed filename (kebab-case `.md`) and the complete markdown content.
   - If NO, explain why.

You MUST output your response in JSON format matching this schema:
{{
  "answer": "Detailed answer in markdown format, with citations to relevant [[pages]].",
  "citations": ["page-name1", "page-name2"],
  "save_as_new_page": true or false,
  "new_page": {{
    "filename": "name-of-new-page.md",
    "title": "Title of the page",
    "content": "Full markdown content of the new page, formatted according to the schema rules (YAML frontmatter, sources list, updated date, content)."
  }},
  "log_entry": "## [{datetime.date.today().isoformat()}] query | Question text summary\\n- Answered question: \\"{question}\\""
}}
"""
    
    client = get_client()
    model = client.GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    
    # Log query operation
    log_path = wiki_dir / "log.md"
    if log_path.exists() and "log_entry" in result:
        log_entry = result["log_entry"].strip()
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        divider_pos = log_content.find("---")
        if divider_pos != -1:
            insert_pos = divider_pos + 3
            log_content = log_content[:insert_pos] + "\n\n" + log_entry + log_content[insert_pos:]
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_content)
                
    return result

def run_save_query_page(filename: str, title: str, content: str, wiki_dir: Path) -> dict:
    """Saves a query answer as a new compounding wiki page and updates the index."""
    page_path = wiki_dir / filename
    
    # Save the page
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
        
    # Update index.md
    index_path = wiki_dir / "index.md"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            idx_content = f.read()
            
        link_search = f"[[{filename.replace('.md', '')}]]"
        if link_search not in idx_content:
            # Place under ## Concepts & Topics
            header_pos = idx_content.find("## Concepts & Topics")
            if header_pos != -1:
                newline_pos = idx_content.find("\n", header_pos)
                placeholder = "*No concepts created yet.*"
                if placeholder in idx_content:
                    idx_content = idx_content.replace(placeholder, "")
                
                addition = f"- [[{filename.replace('.md', '')}]] - Synthesis: {title}"
                idx_content = idx_content[:newline_pos+1] + addition + "\n" + idx_content[newline_pos+1:]
                
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(idx_content)
                    
    # Log the save action
    log_path = wiki_dir / "log.md"
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        divider_pos = log_content.find("---")
        if divider_pos != -1:
            insert_pos = divider_pos + 3
            entry = f"## [{datetime.date.today().isoformat()}] page-saved | {title}\n- Saved synthesis page [[{filename.replace('.md', '')}]]"
            log_content = log_content[:insert_pos] + "\n\n" + entry + log_content[insert_pos:]
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_content)
                
    return {"status": "success", "filename": filename}

def run_lint(wiki_dir: Path, schema_path: Path, model_name=DEFAULT_MODEL) -> dict:
    """Audits the wiki directory to detect broken links, orphans, contradictions, and data gaps."""
    # 1. Read schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
        
    # 2. Get list of files
    wiki_files = list(wiki_dir.glob("*.md"))
    all_filenames = {f.name for f in wiki_files}
    concept_filenames = {f.name.replace(".md", "") for f in wiki_files if f.name not in ["log.md", "index.md"]}
    
    # Structural Linting (computed programmatically)
    broken_links = []
    orphan_candidates = set(concept_filenames)
    page_links = {} # page -> set of outgoing links
    yaml_errors = []
    
    for file_path in wiki_files:
        if file_path.name in ["log.md", "index.md"]:
            continue
            
        page_name = file_path.name.replace(".md", "")
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            # Check YAML frontmatter
            if not content.strip().startswith("---"):
                yaml_errors.append(file_path.name)
            else:
                end_fm = content.find("---", 3)
                if end_fm == -1:
                    yaml_errors.append(file_path.name)
                    
            # Find all double bracket links E.g., [[link-target]] or [[link-target|text]]
            links = re.findall(r'\[\[([^\]|#]+)(?:\|[^\]]*)?(?:#[^\]]*)?\]\]', content)
            
            links_cleaned = set()
            for l in links:
                l_clean = l.strip().lower().replace(" ", "-")
                links_cleaned.add(l_clean)
                
                # Check if file exists
                if l_clean not in concept_filenames and l_clean not in ["index", "log"]:
                    broken_links.append({
                        "source_file": file_path.name,
                        "broken_target": l_clean
                    })
                    
            page_links[page_name] = links_cleaned
            
            # Remove linked pages from orphan candidates
            for l in links_cleaned:
                if l in orphan_candidates:
                    orphan_candidates.remove(l)
                    
        except Exception as e:
            yaml_errors.append(f"{file_path.name} (Error reading: {str(e)})")
            
    # Compile text contents to feed to Gemini for semantic audit
    # We will pass the names and summaries of pages (first few lines) to avoid context bloat if large,
    # or the full content if it is relatively small. Let's send the full content of concept pages (limited to 50k chars).
    semantic_context = []
    total_len = 0
    for file_path in wiki_files:
        if file_path.name in ["log.md", "index.md"]:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            # Just take YAML frontmatter and first 20 lines of content to keep context clean
            text = "".join(lines[:35])
            if len(lines) > 35:
                text += "\n... [content truncated for lint context] ...\n"
            semantic_context.append(f"### Page: {file_path.name}\n{text}")
            total_len += len(text)
            if total_len > 80000:
                break
        except Exception:
            continue
            
    semantic_context_str = "\n\n---\n\n".join(semantic_context)
    
    prompt = f"""
You are the LLMwiki Auditor. Your job is to run a health check on the wiki pages to spot contradictions, outdated claims, missing connections, or data gaps.

Here are the schema rules:
<WIKI_SCHEMA>
{schema_content}
</WIKI_SCHEMA>

Here is the structural analysis compiled by the system:
- **YAML Formatting Errors**: {json.dumps(yaml_errors)}
- **Broken Wiki Links**: {json.dumps(broken_links)}
- **Orphan Pages** (No other pages link to these): {json.dumps(list(orphan_candidates))}

Here is a snippet of each wiki page for your semantic analysis:
<WIKI_PAGES_CONTEXT>
{semantic_context_str}
</WIKI_PAGES_CONTEXT>

Tasks:
1. Examine the contents. Look for semantic issues:
   - **Contradictions**: Any conflicting claims across different pages?
   - **Outdated Claims**: Are older pages making assertions that are contradicted or superseded by newer source summaries?
   - **Missing Cross-References**: Are there pages that discuss a concept but don't link to the corresponding concept page, even though it exists?
   - **Missing Concept Pages**: Are there important terms/concepts frequently mentioned in the texts that do not have their own concept page yet?
2. Generate a prioritized audit list of recommendations. For each recommendation, classify it as "critical" (broken links, major contradiction) or "suggestion" (missing cross-links, new topic idea).

You MUST output your response in JSON format matching this schema:
{{
  "structural_issues": {{
    "yaml_errors": {json.dumps(yaml_errors)},
    "broken_links": {json.dumps(broken_links)},
    "orphans": {json.dumps(list(orphan_candidates))}
  }},
  "semantic_audits": [
    {{
      "issue_type": "contradiction | outdated_claim | missing_link | missing_concept",
      "severity": "critical | suggestion",
      "description": "Details of what is wrong, which pages are involved, and how to fix it."
    }}
  ],
  "suggested_actions": [
     "Specific task description (e.g., 'Link attention-mechanism.md from transformer.md')",
     "..."
  ],
  "log_entry": "## [{datetime.date.today().isoformat()}] lint | Audited wiki\\n- Detected structural issues and semantic recommendations."
}}
"""
    
    client = get_client()
    model = client.GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    
    return result


# ============================================================================
# DATABASE-COMPATIBLE OPERATIONS (for multi-project support)
# ============================================================================
# Note: keep this marker to make Docker rebuilds clearly include latest agent.py changes.

def run_ingest_from_content(source_filename: str, source_content: str, project_id: int, db, model_name=DEFAULT_MODEL) -> dict:
    """Ingests a raw document content into the wiki project using Gemini."""
    from database import WikiPage as WikiPageModel
    
    # Read schema
    schema_path = Path(__file__).resolve().parent / "wiki_schema.md"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
    
    # Read existing index page for context
    index_page = db.query(WikiPageModel).filter(
        WikiPageModel.project_id == project_id,
        WikiPageModel.filename == "index.md"
    ).first()
    index_content = index_page.content if index_page else ""
    
    # Get list of existing pages
    existing_pages = db.query(WikiPageModel).filter(WikiPageModel.project_id == project_id).all()
    existing_filenames = [p.filename for p in existing_pages if p.filename not in ["log.md", "index.md"]]
    
    # Truncate source text if too large
    source_text = source_content
    if len(source_text) > 120000:
        source_text = source_text[:120000] + "\n\n... [Source text truncated for context window size] ..."
    
    # Construct prompt
    prompt = f"""
You are the LLMwiki Programmer. Your job is to ingest a new raw source document into the wiki, obeying the following schema rules:

<WIKI_SCHEMA>
{schema_content}
</WIKI_SCHEMA>

The user has added a new raw source: `{source_filename}`.
Existing wiki pages: {json.dumps(existing_filenames)}

Here is the table of contents (`wiki/index.md`) for context:
<WIKI_INDEX>
{index_content}
</WIKI_INDEX>

Here is the full text of the raw source `{source_filename}`:
<RAW_SOURCE_TEXT>
{source_text}
</RAW_SOURCE_TEXT>

Tasks:
1. Generate a "source-summary" page for this file. Name it based on the document title (kebab-case, e.g., `document-title.md`).
2. Identify which concepts or entities are discussed. For each:
   - Decide whether to CREATE a new concept/entity page (if it doesn't exist) or UPDATE an existing page (if it exists in the list above).
   - Draw information from this new source and synthesize it. Integrate the data. Cite using `(source: {source_filename})`.
   - Maintain Obsidian format (brackets `[[concept-link]]`, lowercase-hyphen names, etc.).
3. Formulate updates for `wiki/index.md` (add the source and new concepts).
4. Create an activity log entry for `wiki/log.md`.

You MUST output your response in JSON format matching this schema:
{{
  "summary_page": {{
    "filename": "summary-filename.md",
    "title": "Title of the source",
    "content": "Full Markdown content for the source summary page complying with the schema."
  }},
  "concept_updates": [
    {{
      "filename": "concept-filename.md",
      "action": "create" or "update",
      "title": "Concept Title",
      "content": "Full markdown content of the concept page. If action is 'update', you must provide the ENTIRE updated content of the file, merging old information."
    }}
  ],
  "log_entry": "## [{datetime.date.today().isoformat()}] ingest | Title of Source\\n- ...",
  "index_updates": {{
    "sources_addition": "- [[summary-filename]] - One-line description of the source.",
    "concepts_addition": [
      "- [[concept-filename]] - One-line description of the concept (only for NEWLY created concepts)."
    ]
  }}
}}

Be extremely thorough. Cite correctly. Make sure filenames are lowercase, kebab-case, and end with `.md`.
Do not include any wrapper other than the JSON block.
"""
    
    client = get_client()
    model = client.GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    
    # Apply changes to database
    modified_files = []
    
    # A. Save summary page
    sum_page = result["summary_page"]
    sum_wiki_page = WikiPageModel(
        project_id=project_id,
        filename=sum_page["filename"],
        title=sum_page["title"],
        content=sum_page["content"].strip() + "\n"
    )
    db.add(sum_wiki_page)
    modified_files.append({"filename": sum_page["filename"], "action": "created", "type": "summary"})
    
    # B. Save/Update concept pages
    for concept in result.get("concept_updates", []):
        filename = concept["filename"]
        
        # Check if page exists
        existing_page = db.query(WikiPageModel).filter(
            WikiPageModel.project_id == project_id,
            WikiPageModel.filename == filename
        ).first()
        
        action = "updated" if existing_page else "created"
        
        if existing_page:
            existing_page.content = concept["content"].strip() + "\n"
            existing_page.title = concept.get("title")
        else:
            new_page = WikiPageModel(
                project_id=project_id,
                filename=filename,
                title=concept.get("title"),
                content=concept["content"].strip() + "\n"
            )
            db.add(new_page)
        
        modified_files.append({"filename": filename, "action": action, "type": "concept"})
    
    # C. Update index.md
    if index_page:
        idx_content = index_page.content
    else:
        idx_content = "# LLMwiki Index\n\n*Compounding Knowledge Base*\n\n---\n\n## Sources\n\n## Concepts & Topics\n\n## Entities (People, Orgs, Projects)\n"
    
    # Insert source
    source_add = result["index_updates"]["sources_addition"]
    link_search = f"[[{sum_page['filename'].replace('.md', '')}]]"
    if link_search not in idx_content:
        header_pos = idx_content.find("## Sources")
        if header_pos != -1:
            newline_pos = idx_content.find("\n", header_pos)
            placeholder = "*No sources ingested yet.*"
            if placeholder in idx_content:
                idx_content = idx_content.replace(placeholder, "")
            idx_content = idx_content[:newline_pos+1] + source_add + "\n" + idx_content[newline_pos+1:]
    
    # Insert concepts
    for concept_add in result["index_updates"].get("concepts_addition", []):
        concept_link = concept_add.split(" - ")[0].strip()
        if concept_link not in idx_content:
            header_pos = idx_content.find("## Concepts & Topics")
            if header_pos != -1:
                newline_pos = idx_content.find("\n", header_pos)
                placeholder = "*No concepts created yet.*"
                if placeholder in idx_content:
                    idx_content = idx_content.replace(placeholder, "")
                idx_content = idx_content[:newline_pos+1] + concept_add + "\n" + idx_content[newline_pos+1:]
    
    # Update or create index page
    if index_page:
        index_page.content = idx_content
    else:
        index_wiki_page = WikiPageModel(
            project_id=project_id,
            filename="index.md",
            title="Index",
            content=idx_content
        )
        db.add(index_wiki_page)
    modified_files.append({"filename": "index.md", "action": "updated", "type": "index"})
    
    # D. Append to log.md
    log_entry = result["log_entry"].strip()
    log_page = db.query(WikiPageModel).filter(
        WikiPageModel.project_id == project_id,
        WikiPageModel.filename == "log.md"
    ).first()
    
    if log_page:
        log_content = log_page.content
    else:
        log_content = "# Activity Log\n\n*Log of all operations performed on LLMwiki (ingests, queries, lints).*\n\n---\n"
    
    divider_pos = log_content.find("---")
    if divider_pos != -1:
        insert_pos = divider_pos + 3
        log_content = log_content[:insert_pos] + "\n\n" + log_entry + log_content[insert_pos:]
    else:
        log_content += "\n\n" + log_entry
    
    if log_page:
        log_page.content = log_content
    else:
        log_wiki_page = WikiPageModel(
            project_id=project_id,
            filename="log.md",
            title="Activity Log",
            content=log_content
        )
        db.add(log_wiki_page)
    modified_files.append({"filename": "log.md", "action": "updated", "type": "log"})
    
    db.commit()
    
    return {
        "summary": sum_page["title"],
        "filename": sum_page["filename"],
        "modified_files": modified_files,
        "raw_source": source_filename
    }


def run_query_from_pages(question: str, pages, schema_path: Path, model_name=DEFAULT_MODEL) -> dict:
    """Queries wiki pages (database objects) and answers using Gemini."""
    # Read schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
    
    # Prepare context from all pages (simplified: no search, just use all)
    context_pages = []
    for page in pages:
        if page.filename not in ["log.md", "index.md"]:
            context_pages.append(f"### Page: {page.filename}\n\n{page.content}")
    
    context_str = "\n\n---\n\n".join(context_pages) if context_pages else "*No wiki pages found.*"
    
    prompt = f"""
You are the LLMwiki Assistant. Your job is to answer a user's question about the knowledge base using the retrieved pages as context.
You must cite the source pages using Obsidian double-bracket wiki-links like `[[page-name]]` or citations like `(source: filename.ext)`.

Here are the schema rules:
<WIKI_SCHEMA>
{schema_content}
</WIKI_SCHEMA>

Here is the wiki context:
<WIKI_CONTEXT>
{context_str}
</WIKI_CONTEXT>

User Question: "{question}"

Instructions:
1. Synthesize a detailed, accurate answer strictly based on the context. If the context does not contain the answer, state so clearly.
2. Provide citations for all key assertions.
3. Suggest if this answer is valuable enough to be saved as a new page in the wiki.
   - If YES, output the proposed filename (kebab-case `.md`) and the complete markdown content.
   - If NO, explain why.

You MUST output your response in JSON format matching this schema:
{{
  "answer": "Detailed answer in markdown format, with citations to relevant [[pages]].",
  "citations": ["page-name1", "page-name2"],
  "save_as_new_page": true or false,
  "new_page": {{
    "filename": "name-of-new-page.md",
    "title": "Title of the page",
    "content": "Full markdown content of the new page, formatted according to the schema rules."
  }},
  "log_entry": "## [{datetime.date.today().isoformat()}] query | Question text summary\\n- Answered question: \\"{question}\\""
}}
"""
    
    client = get_client()
    model = client.GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    return result


def run_lint_from_pages(pages, schema_path: Path, model_name=DEFAULT_MODEL) -> dict:
    """Lints wiki pages (database objects) to detect issues."""
    # Read schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
    
    # Structural linting
    broken_links = []
    orphan_candidates = set()
    yaml_errors = []
    
    all_filenames = {p.filename.replace(".md", "") for p in pages}
    concept_filenames = {p.filename.replace(".md", "") for p in pages if p.filename not in ["log.md", "index.md"]}
    orphan_candidates = concept_filenames.copy()
    
    for page in pages:
        if page.filename in ["log.md", "index.md"]:
            continue
        
        page_name = page.filename.replace(".md", "")
        
        # Check YAML frontmatter
        if not page.content.strip().startswith("---"):
            yaml_errors.append(page.filename)
        else:
            end_fm = page.content.find("---", 3)
            if end_fm == -1:
                yaml_errors.append(page.filename)
        
        # Find wiki links
        links = re.findall(r'\[\[([^\]|#]+)(?:\|[^\]]*)?(?:#[^\]]*)?\]\]', page.content)
        links_cleaned = set()
        for l in links:
            l_clean = l.strip().lower().replace(" ", "-")
            links_cleaned.add(l_clean)
            
            # Check if target exists
            if l_clean not in concept_filenames and l_clean not in ["index", "log"]:
                broken_links.append({
                    "source_file": page.filename,
                    "broken_target": l_clean
                })
        
        # Remove linked pages from orphan candidates
        for l in links_cleaned:
            if l in orphan_candidates:
                orphan_candidates.discard(l)
    
    # Prepare context for semantic analysis
    semantic_context = []
    for page in pages:
        if page.filename in ["log.md", "index.md"]:
            continue
        lines = page.content.split("\n")
        text = "\n".join(lines[:35])
        if len(lines) > 35:
            text += "\n... [content truncated for lint context] ...\n"
        semantic_context.append(f"### Page: {page.filename}\n{text}")
    
    semantic_context_str = "\n\n---\n\n".join(semantic_context)
    
    prompt = f"""
You are the LLMwiki Auditor. Your job is to run a health check on the wiki pages to spot contradictions, outdated claims, missing connections, or data gaps.

Here are the schema rules:
<WIKI_SCHEMA>
{schema_content}
</WIKI_SCHEMA>

Here is the structural analysis:
- **YAML Formatting Errors**: {json.dumps(yaml_errors)}
- **Broken Wiki Links**: {json.dumps(broken_links)}
- **Orphan Pages** (No other pages link to these): {json.dumps(list(orphan_candidates))}

Here is a snippet of each wiki page for semantic analysis:
<WIKI_PAGES_CONTEXT>
{semantic_context_str}
</WIKI_PAGES_CONTEXT>

Tasks:
1. Examine the contents for semantic issues:
   - Contradictions across pages
   - Outdated claims
   - Missing cross-references
   - Missing concept pages
2. Generate a prioritized audit list.

You MUST output your response in JSON format matching this schema:
{{
  "structural_issues": {{
    "yaml_errors": {json.dumps(yaml_errors)},
    "broken_links": {json.dumps(broken_links)},
    "orphans": {json.dumps(list(orphan_candidates))}
  }},
  "semantic_audits": [
    {{
      "issue_type": "contradiction | outdated_claim | missing_link | missing_concept",
      "severity": "critical | suggestion",
      "description": "Details of what is wrong, which pages are involved, and how to fix it."
    }}
  ],
  "suggested_actions": [
    "Specific task description"
  ],
  "log_entry": "## [{datetime.date.today().isoformat()}] lint | Audited wiki\\n- Detected structural issues and semantic recommendations."
}}
"""
    
    client = get_client()
    model = client.GenerativeModel(model_name)
    
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    return result
