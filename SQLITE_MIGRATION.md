# SQLite Migration & Multi-Project Setup Guide

## Overview

Your LLMwiki application has been successfully migrated from file-based storage to **SQLite database** with support for:

✅ **Multi-User Support** - User registration and authentication with JWT tokens  
✅ **Multi-Project Support** - Each user can create and manage multiple wiki projects  
✅ **Project Ownership & Isolation** - Projects are fully isolated by owner  
✅ **Wiki Sharing** - Share projects with others with read-only or read-write permissions  
✅ **Secure Access Control** - All endpoints protected by authentication  

---

## Architecture Changes

### Database Models

**Users**
- `id` (primary key)
- `username` (unique)
- `email` (unique)
- `password_hash`
- `created_at`

**Projects**
- `id` (primary key)
- `name`
- `description`
- `owner_id` (foreign key → Users)
- `created_at`, `updated_at`

**ProjectMemberships** (Sharing)
- `id` (primary key)
- `project_id` (foreign key → Projects)
- `user_id` (foreign key → Users)
- `permission_level` (read_only | read_write)
- `created_at`

**WikiPages**
- `id` (primary key)
- `project_id` (foreign key → Projects)
- `filename`
- `title`
- `content`
- `created_at`, `updated_at`

**RawDocuments**
- `id` (primary key)
- `project_id` (foreign key → Projects)
- `filename`
- `content`
- `size`
- `uploaded_at`

### Database Storage

- **File**: `llmwiki.db` (created automatically in project root)
- **Type**: SQLite 3
- **Auto-Initialize**: Yes (on app startup)

---

## New Endpoints

### Authentication

```
POST /api/auth/register
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password"
}
→ Returns: { access_token, token_type, user }

POST /api/auth/login
{
  "username": "john_doe",
  "password": "secure_password"
}
→ Returns: { access_token, token_type, user }

GET /api/auth/me
→ Returns: { id, username, email, created_at }
```

All authenticated endpoints require an `Authorization: Bearer <token>` header.

### Project Management

```
POST /api/projects
{
  "name": "AI Research Wiki",
  "description": "Research notes on AI topics"
}
→ Returns: Project object

GET /api/projects
→ Returns: List of owned + shared projects

GET /api/projects/{project_id}
→ Returns: Project details (must be owner or member)

PUT /api/projects/{project_id}
{
  "name": "Updated Name",
  "description": "Updated description"
}
→ Returns: Updated project (owner only)

DELETE /api/projects/{project_id}
→ Deletes project (owner only)

POST /api/projects/{project_id}/share
{
  "username": "other_user",
  "permission_level": "read_write"  # or "read_only"
}
→ Shares project with user

DELETE /api/projects/{project_id}/share/{username}
→ Removes access for user (owner only)
```

### Wiki Operations (Project-Scoped)

**All wiki endpoints now require a `project_id` parameter:**

```
GET /api/projects/{project_id}/files/wiki
→ List wiki pages in project

GET /api/projects/{project_id}/files/wiki/{filename}
→ Read a wiki page

POST /api/projects/{project_id}/files/wiki/{filename}
→ Create/update a wiki page

GET /api/projects/{project_id}/files/raw
→ List raw documents in project

POST /api/projects/{project_id}/files/raw/upload
→ Upload raw document to project

POST /api/projects/{project_id}/ingest
{ "filename": "source.pdf", "model": "gemini-flash-lite-latest" }
→ Ingest raw doc into wiki

POST /api/projects/{project_id}/query
{ "question": "What is...", "model": "gemini-flash-lite-latest" }
→ Query the wiki

POST /api/projects/{project_id}/query/save
{ "filename": "answer.md", "title": "Answer", "content": "..." }
→ Save query result as page

POST /api/projects/{project_id}/lint
{ "model": "gemini-flash-lite-latest" }
→ Audit wiki for issues

GET /api/projects/{project_id}/graph
→ Get graph visualization data
```

---

## Usage Flow

### 1. Register & Login

```javascript
// Register
const registerRes = await fetch('/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'jane',
    email: 'jane@example.com',
    password: 'mypassword'
  })
});
const { access_token } = await registerRes.json();
localStorage.setItem('token', access_token);

// All future requests include token
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};
```

### 2. Create a Project

```javascript
const res = await fetch('/api/projects', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    name: 'My First Wiki',
    description: 'Research and notes'
  })
});
const project = await res.json();
const projectId = project.id;
```

### 3. Upload & Ingest

```javascript
// Upload raw document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadRes = await fetch(`/api/projects/${projectId}/files/raw/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },  // Don't set Content-Type for FormData
  body: formData
});

// Ingest into wiki
const ingestRes = await fetch(`/api/projects/${projectId}/ingest`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    filename: 'document.pdf',
    model: 'gemini-flash-lite-latest'
  })
});
const result = await ingestRes.json();
```

### 4. Query & Share

```javascript
// Query
const queryRes = await fetch(`/api/projects/${projectId}/query`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    question: 'What are the key concepts?',
    model: 'gemini-flash-lite-latest'
  })
});

// Share project
const shareRes = await fetch(`/api/projects/${projectId}/share`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    username: 'other_user',
    permission_level: 'read_write'
  })
});
```

---

## Permission Levels

**read_only**
- View wiki pages
- View raw documents
- Run queries
- View graph

**read_write**
- Everything in read_only, plus:
- Upload raw documents
- Create/edit wiki pages
- Run ingest operations
- Save query results

**Owner**
- Everything in read_write, plus:
- Update project details
- Delete project
- Share/unshare with others
- Change permission levels

---

## Frontend Updates Needed

Your frontend (`app.js`, `index.html`) needs updates to:

1. **Add Auth UI**
   - Login/Register forms
   - Token storage/retrieval
   - Logout button

2. **Add Project UI**
   - Project dashboard/list
   - Create new project modal
   - Project selector dropdown
   - Share project dialog

3. **Update API Calls**
   - Include `Authorization` header on all requests
   - Update URLs to include `project_id`
   - Example: `/api/files/wiki` → `/api/projects/{projectId}/files/wiki`

4. **Persist Token**
   - Store JWT in localStorage
   - Retrieve on page load
   - Set Authorization header globally

---

## Environment Variables

Add to `.env` file:

```env
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=your-secret-key-change-in-production
```

The `SECRET_KEY` is used for JWT signing. Change in production!

---

## Running the Application

```bash
# Start virtual environment
.venv\Scripts\Activate.ps1

# Start server
python server.py

# Access at http://localhost:8000
```

The database (`llmwiki.db`) is created automatically on first startup.

---

## Data Migration from File-Based to SQLite

The old file-based wiki and raw documents are NOT automatically migrated. To migrate existing data:

1. **Preserve raw files** in `raw/` directory
2. **Create a new project** via the API
3. **Upload and ingest** raw files one by one
4. **Manually review** existing wiki pages and re-create them in the database

This ensures data integrity and allows you to restructure as needed.

---

## Backward Compatibility

The following endpoints remain **unchanged**:

```
GET /api/config
POST /api/config
GET / (HTML)
GET /styles.css
GET /app.js
```

All other endpoints have been refactored for multi-project support and now require authentication + project_id.

---

## Next Steps

1. ✅ **Database initialized** - SQLite is set up
2. ✅ **Authentication ready** - Register/login working
3. ✅ **Project management** - Create/manage projects
4. ⏳ **Frontend updates** - Update HTML/JS for new UI flows
5. ⏳ **Data migration** - Move existing wiki content to new system
6. ⏳ **Testing** - Test all workflows end-to-end

---

## Troubleshooting

**"Database locked" error**
- Ensure only one instance of the server is running
- Close other connections to `llmwiki.db`

**"Invalid token" error**
- Token may have expired (set to 30 minutes by default)
- Re-login to get a new token
- Change `ACCESS_TOKEN_EXPIRE_MINUTES` in `auth.py` to adjust

**"Access denied" error**
- You don't own the project
- You're not a member of the shared project
- Your membership permission level is insufficient (e.g., read_only on write operation)

**Gemini API errors**
- Check `GEMINI_API_KEY` is set correctly
- Verify API key has quota remaining
- Check internet connectivity

---

## Questions?

Refer to the database models in `database.py` and auth logic in `auth.py` for detailed implementation.
