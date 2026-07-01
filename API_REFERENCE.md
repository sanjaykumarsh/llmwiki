# LLMwiki Multi-Project API Quick Reference

## Base URL
`http://localhost:8000`

## Authentication
All endpoints except `/api/config` require:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

---

## Authentication Endpoints

### Register
```
POST /api/auth/register
Body: { "username": "str", "email": "str", "password": "str" }
Returns: { "access_token": "str", "token_type": "bearer", "user": {...} }
Auth: None
```

### Login
```
POST /api/auth/login
Body: { "username": "str", "password": "str" }
Returns: { "access_token": "str", "token_type": "bearer", "user": {...} }
Auth: None
```

### Get Current User
```
GET /api/auth/me
Returns: { "id": int, "username": "str", "email": "str", "created_at": "datetime" }
Auth: Required
```

---

## Project Management

### Create Project
```
POST /api/projects
Body: { "name": "str", "description": "str?" }
Returns: Project { id, name, description, owner_id, created_at, is_owner }
Auth: Required
```

### List Projects
```
GET /api/projects
Returns: [ Project, ... ]  // Owned + shared projects
Auth: Required
```

### Get Project
```
GET /api/projects/{project_id}
Returns: Project
Auth: Required (must be owner or member)
```

### Update Project
```
PUT /api/projects/{project_id}
Body: { "name": "str?", "description": "str?" }
Returns: Project
Auth: Required (owner only)
```

### Delete Project
```
DELETE /api/projects/{project_id}
Returns: { "status": "success", "message": "str" }
Auth: Required (owner only)
```

### Share Project
```
POST /api/projects/{project_id}/share
Body: { "username": "str", "permission_level": "read_only|read_write" }
Returns: { "status": "success", "message": "str" }
Auth: Required (owner only)
```

### Unshare Project
```
DELETE /api/projects/{project_id}/share/{username}
Returns: { "status": "success", "message": "str" }
Auth: Required (owner only)
```

---

## Wiki Page Management

### List Wiki Pages
```
GET /api/projects/{project_id}/files/wiki
Returns: [ { id, name, title, size, updated_at }, ... ]
Auth: Required (member of project)
```

### Read Wiki Page
```
GET /api/projects/{project_id}/files/wiki/{filename}
Returns: { id, filename, title, content }
Auth: Required (member of project)
```

### Create/Update Wiki Page
```
POST /api/projects/{project_id}/files/wiki/{filename}
Body: FormData { content: "str" }
Returns: { "status": "success", "id": int, "filename": "str" }
Auth: Required (owner or read_write member)
```

---

## Raw Document Management

### List Raw Documents
```
GET /api/projects/{project_id}/files/raw
Returns: [ { id, name, size, uploaded_at }, ... ]
Auth: Required (member of project)
```

### Upload Raw Document
```
POST /api/projects/{project_id}/files/raw/upload
Body: FormData { file: File }
Returns: { "status": "success", "id": int, "filename": "str", "size": int }
Auth: Required (owner or read_write member)
```

---

## AI Operations

### Ingest Raw Document
```
POST /api/projects/{project_id}/ingest
Body: { "filename": "str", "model": "str?" }
Returns: { "summary": "str", "filename": "str", "modified_files": [...] }
Auth: Required (owner or read_write member)
Note: Requires GEMINI_API_KEY configured
```

### Query Wiki
```
POST /api/projects/{project_id}/query
Body: { "question": "str", "model": "str?" }
Returns: { "answer": "str", "citations": [...], "save_as_new_page": bool, "new_page": {...} }
Auth: Required (member of project)
Note: Requires GEMINI_API_KEY configured
```

### Save Query Result as Wiki Page
```
POST /api/projects/{project_id}/query/save
Body: { "filename": "str", "title": "str", "content": "str" }
Returns: { "status": "success", "filename": "str" }
Auth: Required (owner or read_write member)
```

### Lint Wiki
```
POST /api/projects/{project_id}/lint
Body: { "model": "str?" }
Returns: { "structural_issues": {...}, "semantic_audits": [...], "suggested_actions": [...] }
Auth: Required (member of project)
Note: Requires GEMINI_API_KEY configured
```

### Get Graph Visualization Data
```
GET /api/projects/{project_id}/graph
Returns: { "nodes": [...], "links": [...] }
Auth: Required (member of project)
```

---

## Configuration (No Auth Required)

### Get Config
```
GET /api/config
Returns: { "api_key_configured": bool, "masked_key": "str", "default_model": "str" }
```

### Set Config
```
POST /api/config
Body: { "api_key": "str" }
Returns: { "status": "success", "message": "str" }
```

---

## Permission Levels

| Permission | View Pages | View Graphs | Query | Upload Docs | Ingest | Edit Pages | Manage Project |
|-----------|-----------|-----------|-------|-----------|--------|-----------|---|
| read_only | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| read_write | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| owner | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Error Codes

```
200 OK - Request successful
400 Bad Request - Invalid input
401 Unauthorized - Missing/invalid token
403 Forbidden - No permission for operation
404 Not Found - Resource doesn't exist
500 Internal Server Error - Server error
```

---

## Example Request/Response

### Register
**Request:**
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

### Create Project
**Request:**
```
POST /api/projects
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "AI Research",
  "description": "Research notes on AI/ML topics"
}
```

**Response (200):**
```json
{
  "id": 42,
  "name": "AI Research",
  "description": "Research notes on AI/ML topics",
  "owner_id": 1,
  "created_at": "2024-01-15T10:35:00",
  "is_owner": true
}
```

### Query Wiki
**Request:**
```
POST /api/projects/42/query
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "question": "What are transformers?",
  "model": "gemini-flash-lite-latest"
}
```

**Response (200):**
```json
{
  "answer": "Transformers are a type of neural network architecture... [[attention-mechanism]] ...",
  "citations": ["transformer-architecture", "attention-mechanism"],
  "save_as_new_page": false,
  "log_entry": "## [2024-01-15] query | What are transformers?..."
}
```

---

## Implementation Notes

### Token Management
- Tokens expire after 30 minutes
- Store token in browser localStorage or secure cookie
- Include in Authorization header for all authenticated requests
- Format: `Authorization: Bearer <token>`

### File Uploads
- Use `FormData` for file uploads
- Don't set `Content-Type` header (browser will set multipart/form-data)
- Max file size: Depends on server config (default unlimited)

### Models
- Default: `gemini-flash-lite-latest`
- Available: Any Google Generative AI model (e.g., `gemini-1.5-pro`)

### Response Format
- All responses are JSON (except static files)
- Timestamps in ISO 8601 format
- Errors include `detail` field with message

---

## Status Codes by Endpoint

### Authentication
- 200: Success
- 400: Invalid credentials or user exists
- 500: Server error

### Projects
- 200: Success
- 403: Not owner/member
- 404: Project not found
- 500: Server error

### Wiki Operations
- 200: Success
- 403: No read_write permission (on write)
- 404: Page/document not found
- 500: Server error (e.g., Gemini API unavailable)

---

## Rate Limiting
Not implemented by default. Add rate limiting middleware for production:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

---

## CORS
Configured to allow all origins for development. Restrict in production:
```python
CORSMiddleware(
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)
```
