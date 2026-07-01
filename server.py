import os
from pathlib import Path
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn
import re
from datetime import datetime, timedelta
from io import BytesIO

from pypdf import PdfReader

import agent
from database import engine, Base, SessionLocal, User, Project, ProjectMembership, WikiPage, RawDocument, PermissionLevel, get_db, init_db
from auth import (
    get_current_user, create_access_token, authenticate_user, register_user,
    UserSchema, UserRegisterSchema, UserLoginSchema, TokenSchema, ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="LLMwiki Server")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"
SCHEMA_PATH = BASE_DIR / "wiki_schema.md"

# Ensure directories exist (for file-based legacy support if needed)
RAW_DIR.mkdir(exist_ok=True)
WIKI_DIR.mkdir(exist_ok=True)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database on application startup"""
    init_db()
    
    # Load .env on startup
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        key, val = line.strip().split("=", 1)
                        if key == "GEMINI_API_KEY":
                            os.environ["GEMINI_API_KEY"] = val
                            agent.get_client()
        except Exception as e:
            print(f"Error loading .env on startup: {e}")
    
    print("✓ Database initialized")


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class QueryRequest(BaseModel):
    question: str
    model: str = agent.DEFAULT_MODEL

class SaveQueryRequest(BaseModel):
    filename: str
    title: str
    content: str

class IngestRequest(BaseModel):
    filename: str
    model: str = agent.DEFAULT_MODEL

class LintRequest(BaseModel):
    model: str = agent.DEFAULT_MODEL

class ConfigSaveRequest(BaseModel):
    api_key: str

class ProjectCreateRequest(BaseModel):
    name: str
    description: str = ""

class ProjectUpdateRequest(BaseModel):
    name: str = None
    description: str = None

class ProjectShareRequest(BaseModel):
    username: str
    permission_level: PermissionLevel

class ProjectSchema(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    created_at: datetime
    is_owner: bool = False
    permission_level: str = None
    
    class Config:
        from_attributes = True

class ProjectMemberSchema(BaseModel):
    username: str
    email: str
    is_owner: bool
    permission_level: str

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def get_index():
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_file)

@app.get("/styles.css")
def get_styles():
    css_file = BASE_DIR / "styles.css"
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="styles.css not found")
    return FileResponse(css_file, media_type="text/css")

@app.get("/app.js")
def get_app_js():
    js_file = BASE_DIR / "app.js"
    if not js_file.exists():
        raise HTTPException(status_code=404, detail="app.js not found")
    return FileResponse(js_file, media_type="application/javascript")


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register", response_model=TokenSchema)
def register(req: UserRegisterSchema, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = register_user(req.username, req.email, req.password, db)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserSchema.from_orm(user)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=TokenSchema)
def login(req: UserLoginSchema, db: Session = Depends(get_db)):
    """Login user"""
    user = authenticate_user(req.username, req.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserSchema.from_orm(user)
    }

@app.get("/api/auth/me", response_model=UserSchema)
def get_current_user_endpoint(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return UserSchema.from_orm(current_user)

# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/projects", response_model=ProjectSchema)
def create_project(
    req: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new wiki project"""
    project = Project(
        name=req.name,
        description=req.description,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    result = ProjectSchema.from_orm(project)
    result.is_owner = True
    return result

@app.get("/api/projects", response_model=list[ProjectSchema])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects accessible by the current user (owned + shared)"""
    # Get owned projects
    owned_projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    
    # Get shared projects
    memberships = db.query(ProjectMembership).filter(ProjectMembership.user_id == current_user.id).all()
    shared_projects = [m.project for m in memberships]
    
    # Combine and format
    projects = []
    for project in owned_projects:
        p = ProjectSchema.from_orm(project)
        p.is_owner = True
        projects.append(p)
    
    for project in shared_projects:
        p = ProjectSchema.from_orm(project)
        p.is_owner = False
        # Find the membership to get permission level
        membership = db.query(ProjectMembership).filter(
            ProjectMembership.user_id == current_user.id,
            ProjectMembership.project_id == project.id
        ).first()
        if membership:
            p.permission_level = membership.permission_level.value
        projects.append(p)
    
    return projects

@app.get("/api/projects/{project_id}", response_model=ProjectSchema)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project (must be owner or have access)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions
    if project.owner_id != current_user.id:
        membership = db.query(ProjectMembership).filter(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == current_user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")
    
    result = ProjectSchema.from_orm(project)
    result.is_owner = (project.owner_id == current_user.id)
    return result

@app.put("/api/projects/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    req: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project (owner only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can update project")
    
    if req.name:
        project.name = req.name
    if req.description is not None:
        project.description = req.description
    
    db.commit()
    db.refresh(project)
    
    result = ProjectSchema.from_orm(project)
    result.is_owner = True
    return result

@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project (owner only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete project")
    
    db.delete(project)
    db.commit()
    
    return {"status": "success", "message": "Project deleted"}

@app.post("/api/projects/{project_id}/share")
def share_project(
    project_id: int,
    req: ProjectShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Share a project with another user (owner only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can share project")
    
    # Find target user
    target_user = db.query(User).filter(User.username == req.username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")
    
    # Check if already shared
    existing = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == target_user.id
    ).first()
    
    if existing:
        # Update permission level
        existing.permission_level = req.permission_level
    else:
        # Create new membership
        membership = ProjectMembership(
            project_id=project_id,
            user_id=target_user.id,
            permission_level=req.permission_level
        )
        db.add(membership)
    
    db.commit()
    return {"status": "success", "message": f"Project shared with {req.username}"}

@app.delete("/api/projects/{project_id}/share/{username}")
def unshare_project(
    project_id: int,
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove access to a project for another user (owner only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can unshare project")
    
    target_user = db.query(User).filter(User.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == target_user.id
    ).first()
    
    if membership:
        db.delete(membership)
        db.commit()
    
    return {"status": "success", "message": "Access removed"}

@app.get("/api/projects/{project_id}/members", response_model=list[ProjectMemberSchema])
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List project members for a project the user can access"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    members = [
        ProjectMemberSchema(
            username=project.owner.username,
            email=project.owner.email,
            is_owner=True,
            permission_level=PermissionLevel.READ_WRITE.value
        )
    ]

    memberships = db.query(ProjectMembership).filter(ProjectMembership.project_id == project_id).all()
    for membership in memberships:
        if membership.user_id == project.owner_id:
            continue
        members.append(
            ProjectMemberSchema(
                username=membership.user.username,
                email=membership.user.email,
                is_owner=False,
                permission_level=membership.permission_level.value
            )
        )

    return members

@app.post("/api/config")
def save_config(req: ConfigSaveRequest):
    """Save API configuration"""
    try:
        api_key = req.api_key.strip()
        if not api_key:
            raise HTTPException(status_code=400, detail="API Key cannot be empty")
        
        # Set in environment
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Persist to local .env file
        env_file = BASE_DIR / ".env"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={api_key}\n")
        
        # Re-configure the agent module
        agent.get_client()
        
        return {"status": "success", "message": "API key updated and saved to .env"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTION: CHECK PROJECT ACCESS
# ============================================================================

def check_project_access(project_id: int, user: User, db: Session, required_level: PermissionLevel = None):
    """
    Check if user has access to a project.
    Returns (has_access, is_owner, permission_level)
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return (False, False, None)
    
    is_owner = (project.owner_id == user.id)
    if is_owner:
        return (True, True, PermissionLevel.READ_WRITE)
    
    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == user.id
    ).first()
    
    if membership:
        if required_level and membership.permission_level != required_level:
            return (True, False, membership.permission_level)
        return (True, False, membership.permission_level)
    
    return (False, False, None)


# ============================================================================
# CONFIG API
# ============================================================================

@app.get("/api/config")
def get_config():
    """Get API configuration (without requiring authentication)"""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    # Mask API Key for security
    masked_key = ""
    if api_key:
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "Configured"
    return {
        "api_key_configured": bool(api_key),
        "masked_key": masked_key,
        "default_model": agent.DEFAULT_MODEL
    }

# ============================================================================
# RAW DOCUMENTS API (PROJECT-SCOPED)
# ============================================================================

@app.get("/api/projects/{project_id}/files/raw")
def list_raw_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List raw documents in a project"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    documents = db.query(RawDocument).filter(RawDocument.project_id == project_id).all()
    return [
        {
            "id": doc.id,
            "name": doc.filename,
            "size": doc.size,
            "uploaded_at": doc.uploaded_at
        }
        for doc in documents
    ]

@app.post("/api/projects/{project_id}/files/raw/upload")
async def upload_raw_file(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a raw document to a project"""
    has_access, is_owner, perm_level = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check write permission
    if not is_owner and perm_level != PermissionLevel.READ_WRITE:
        raise HTTPException(status_code=403, detail="You don't have write access")
    
    try:
        contents = await file.read()

        filename_lower = (file.filename or "").lower()
        decoded_content = ""

        if filename_lower.endswith(".pdf"):
            try:
                reader = PdfReader(BytesIO(contents))
                decoded_content = "\n\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception:
                decoded_content = contents.decode("utf-8", errors="ignore")
        elif filename_lower.endswith(".docx"):
            # DOCX is a zip archive of XML files. Extract readable paragraph text from document.xml.
            try:
                import zipfile
                import xml.etree.ElementTree as ET

                with zipfile.ZipFile(BytesIO(contents)) as zf:
                    with zf.open("word/document.xml") as doc_xml:
                        xml_data = doc_xml.read()

                root = ET.fromstring(xml_data)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for para in root.findall(".//w:p", ns):
                    runs = [t.text for t in para.findall(".//w:t", ns) if t.text]
                    line = "".join(runs).strip()
                    if line:
                        paragraphs.append(line)
                decoded_content = "\n".join(paragraphs)
            except Exception:
                decoded_content = contents.decode("utf-8", errors="ignore")
        else:
            decoded_content = contents.decode("utf-8", errors="ignore")

        if not decoded_content.strip():
            decoded_content = "[No extractable text content found in uploaded file]"
        
        # Save to database
        raw_doc = RawDocument(
            project_id=project_id,
            filename=file.filename,
            content=decoded_content,
            size=len(contents)
        )
        db.add(raw_doc)
        db.commit()
        db.refresh(raw_doc)
        
        return {
            "status": "success",
            "id": raw_doc.id,
            "filename": file.filename,
            "size": len(contents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WIKI PAGES API (PROJECT-SCOPED)
# ============================================================================

@app.get("/api/projects/{project_id}/files/wiki")
def list_wiki_pages(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List wiki pages in a project"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pages = db.query(WikiPage).filter(WikiPage.project_id == project_id).all()
    result = [
        {
            "id": page.id,
            "name": page.filename,
            "title": page.title or page.filename,
            "size": len(page.content),
            "updated_at": page.updated_at
        }
        for page in pages
    ]
    # Sort index and log to the top
    result.sort(key=lambda x: (x["name"] not in ["index.md", "log.md"], x["name"]))
    return result

@app.get("/api/projects/{project_id}/files/wiki/{filename}")
def read_wiki_page(
    project_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Read a wiki page"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Security check
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=403, detail="Invalid filename")
    
    page = db.query(WikiPage).filter(
        WikiPage.project_id == project_id,
        WikiPage.filename == filename
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail=f"Wiki page {filename} not found")
    
    return {
        "id": page.id,
        "filename": page.filename,
        "title": page.title,
        "content": page.content
    }

@app.post("/api/projects/{project_id}/files/wiki/{filename}")
def write_wiki_page(
    project_id: int,
    filename: str,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Write/update a wiki page"""
    has_access, is_owner, perm_level = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check write permission
    if not is_owner and perm_level != PermissionLevel.READ_WRITE:
        raise HTTPException(status_code=403, detail="You don't have write access")
    
    # Security check
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=403, detail="Invalid filename")
    
    try:
        page = db.query(WikiPage).filter(
            WikiPage.project_id == project_id,
            WikiPage.filename == filename
        ).first()
        
        if page:
            page.content = content.strip() + "\n"
        else:
            page = WikiPage(
                project_id=project_id,
                filename=filename,
                content=content.strip() + "\n"
            )
            db.add(page)
        
        db.commit()
        db.refresh(page)
        
        return {
            "status": "success",
            "id": page.id,
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GRAPH API (PROJECT-SCOPED)
# ============================================================================

@app.get("/api/projects/{project_id}/graph")
def get_graph_data(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get graph data for wiki visualization"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        nodes = []
        links = []
        
        pages = db.query(WikiPage).filter(WikiPage.project_id == project_id).all()
        concept_filenames = {p.filename.replace(".md", "") for p in pages}
        
        for page in pages:
            name_id = page.filename.replace(".md", "")
            title = page.title or name_id
            page_type = "concept"
            
            if page.filename == "index.md":
                page_type = "core"
                title = "Index"
            elif page.filename == "log.md":
                page_type = "core"
                title = "Log"
            
            nodes.append({
                "id": name_id,
                "title": title,
                "type": page_type
            })
            
            # Find wiki links
            outlinks = re.findall(r'\[\[([^\]|#\n]+)(?:\|[^\]\n]*)?(?:#[^\]\n]*)?\]\]', page.content)
            for target in outlinks:
                target_clean = target.strip().lower().replace(" ", "-")
                if target_clean in concept_filenames:
                    links.append({
                        "source": name_id,
                        "target": target_clean
                    })
        
        return {"nodes": nodes, "links": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AGENT OPERATIONS APIS (PROJECT-SCOPED)
# ============================================================================

@app.post("/api/projects/{project_id}/ingest")
def ingest_file(
    project_id: int,
    req: IngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a raw document into the wiki"""
    has_access, is_owner, perm_level = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check write permission
    if not is_owner and perm_level != PermissionLevel.READ_WRITE:
        raise HTTPException(status_code=403, detail="You don't have write access")
    
    if not os.environ.get("GEMINI_API_KEY", ""):
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured. Please set it in Settings.")
    
    try:
        # Get the raw document
        raw_doc = db.query(RawDocument).filter(
            RawDocument.project_id == project_id,
            RawDocument.filename == req.filename
        ).first()
        
        if not raw_doc:
            raise FileNotFoundError(f"Raw document {req.filename} not found")
        
        # Run ingest using agent
        result = agent.run_ingest_from_content(
            source_filename=req.filename,
            source_content=raw_doc.content,
            project_id=project_id,
            db=db,
            model_name=req.model
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/projects/{project_id}/query")
def query_wiki(
    project_id: int,
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query the wiki in a project"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.environ.get("GEMINI_API_KEY", ""):
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured. Please set it in Settings.")
    
    try:
        # Get all wiki pages for this project
        pages = db.query(WikiPage).filter(WikiPage.project_id == project_id).all()
        
        result = agent.run_query_from_pages(
            question=req.question,
            pages=pages,
            schema_path=SCHEMA_PATH,
            model_name=req.model
        )
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/api/projects/{project_id}/query/save")
def save_query_page(
    project_id: int,
    req: SaveQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save a query result as a wiki page"""
    has_access, is_owner, perm_level = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check write permission
    if not is_owner and perm_level != PermissionLevel.READ_WRITE:
        raise HTTPException(status_code=403, detail="You don't have write access")
    
    try:
        page = db.query(WikiPage).filter(
            WikiPage.project_id == project_id,
            WikiPage.filename == req.filename
        ).first()
        
        if page:
            page.content = req.content.strip() + "\n"
            page.title = req.title
        else:
            page = WikiPage(
                project_id=project_id,
                filename=req.filename,
                title=req.title,
                content=req.content.strip() + "\n"
            )
            db.add(page)
        
        db.commit()
        return {"status": "success", "filename": req.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/lint")
def lint_wiki(
    project_id: int,
    req: LintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lint the wiki in a project"""
    has_access, _, _ = check_project_access(project_id, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.environ.get("GEMINI_API_KEY", ""):
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured. Please set it in Settings.")
    
    try:
        # Get all wiki pages for this project
        pages = db.query(WikiPage).filter(WikiPage.project_id == project_id).all()
        
        result = agent.run_lint_from_pages(
            pages=pages,
            schema_path=SCHEMA_PATH,
            model_name=req.model
        )
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lint failed: {str(e)}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload_enabled = os.environ.get("RELOAD", "false").lower() == "true"
    uvicorn.run("server:app", host=host, port=port, reload=reload_enabled)
