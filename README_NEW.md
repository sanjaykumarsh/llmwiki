# LLMwiki - Multi-User, Multi-Project Edition

A collaborative wiki application powered by Generative AI (Google Gemini), now with **SQLite database support**, **multi-user authentication**, **multi-project management**, and **team collaboration** features.

## What's New ✨

### v2.0: SQLite & Multi-Project Support
- ✅ **User Authentication** - Secure registration and JWT-based login
- ✅ **Multi-Project Support** - Each user can create multiple wikis  
- ✅ **Project Sharing** - Share wikis with team members with granular permissions
- ✅ **Permission Levels** - Read-only or read-write access control
- ✅ **SQLite Database** - Persistent storage with automatic schema management
- ✅ **Full Project Isolation** - Complete data separation between projects and users

### Existing Features (Preserved)
- AI-powered wiki ingestion (Google Gemini)
- Wiki page management (markdown)
- Raw document upload and processing
- Graph-based wiki visualization
- Wiki querying with semantic search
- Wiki linting and quality audits
- Markdown-based knowledge graphs

---

## Quick Start

### 1. Prerequisites
- Python 3.9+
- pip
- Google Gemini API key (free tier available)

### 2. Installation
```bash
# Clone or download the project
cd llmwiki

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in project root:
```env
GEMINI_API_KEY=your-api-key-here
SECRET_KEY=change-this-in-production
```

Get your free Gemini API key: https://ai.google.dev/

### 4. Run
```bash
python server.py
```

Access at: http://localhost:8000

---

## Usage

### Option A: Use the Python Client
```bash
python client_example.py --demo
```

Or interactively:
```bash
python client_example.py
> register john john@example.com password123
> create-project AI Research
> list-projects
```

### Option B: Use the Frontend (requires update)
Access http://localhost:8000 and use the web interface
(Note: Frontend needs updates for auth UI and project management)

### Option C: Use curl
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "secure_password"
  }'

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Wiki", "description": "Research notes"}'
```

---

## Architecture

### Database Schema
```
Users
├── id (primary key)
├── username (unique)
├── email (unique)
├── password_hash
└── created_at

Projects
├── id (primary key)
├── name
├── description
├── owner_id (FK → Users)
├── created_at
└── updated_at

ProjectMemberships (Sharing)
├── id (primary key)
├── project_id (FK → Projects)
├── user_id (FK → Users)
├── permission_level (read_only | read_write)
└── created_at

WikiPages
├── id (primary key)
├── project_id (FK → Projects)
├── filename
├── title
├── content
├── created_at
└── updated_at

RawDocuments
├── id (primary key)
├── project_id (FK → Projects)
├── filename
├── content
├── size
└── uploaded_at
```

### Tech Stack
- **Backend**: FastAPI + Uvicorn
- **Database**: SQLite (can upgrade to PostgreSQL)
- **Auth**: JWT tokens + bcrypt password hashing
- **AI**: Google Generative AI (Gemini)
- **Frontend**: HTML/CSS/JavaScript (needs update for new features)

---

## API Overview

### Authentication (20 lines to use)
```javascript
// Register
const res = await fetch('/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user',
    email: 'user@example.com',
    password: 'password'
  })
});
const { access_token } = await res.json();
```

### Project Management
```javascript
// Create project
const token = localStorage.getItem('token');
const project = await fetch('/api/projects', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'My Wiki',
    description: 'Research notes'
  })
}).then(r => r.json());

// Share project
await fetch(`/api/projects/${project.id}/share`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'colleague',
    permission_level: 'read_write'
  })
});
```

### Wiki Operations (All project-scoped)
```javascript
const projectId = project.id;

// Upload raw document
const formData = new FormData();
formData.append('file', document);
await fetch(`/api/projects/${projectId}/files/raw/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

// Ingest into wiki
await fetch(`/api/projects/${projectId}/ingest`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ filename: 'document.pdf' })
});

// Query wiki
const answer = await fetch(`/api/projects/${projectId}/query`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: 'What is X?' })
}).then(r => r.json());
```

---

## File Structure
```
llmwiki/
├── server.py              # FastAPI server with all endpoints
├── agent.py               # AI operations (ingest, query, lint)
├── database.py            # SQLAlchemy models & initialization
├── auth.py                # JWT authentication logic
├── app.js                 # Frontend JavaScript (needs update)
├── index.html             # Frontend HTML (needs update)
├── styles.css             # Frontend CSS
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (create this)
├── llmwiki.db             # SQLite database (auto-created)
│
├── wiki/                  # Wiki pages (markdown files)
├── raw/                   # Raw documents (for testing)
│
├── API_REFERENCE.md       # Complete API documentation
├── SQLITE_MIGRATION.md    # Migration guide
├── CHANGES.md             # Detailed changelog
├── IMPLEMENTATION_STATUS.md # Status and next steps
├── client_example.py      # Example Python client
└── README.md              # This file
```

---

## Documentation

- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete endpoint documentation with examples
- **[SQLITE_MIGRATION.md](SQLITE_MIGRATION.md)** - Migration guide, architecture details, usage flows
- **[CHANGES.md](CHANGES.md)** - Detailed list of all modifications
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Current status, completed tasks, remaining work

---

## Key Features

### 🔐 Security
- Passwords hashed with bcrypt
- JWT token-based authentication
- Granular permission levels
- Project isolation at database level
- Input validation with Pydantic

### 👥 Multi-User
- User registration and login
- JWT token authentication
- Session persistence
- Automatic token expiration

### 📁 Multi-Project
- Create unlimited projects
- Full project ownership
- Share projects with team members
- Two permission levels (read-only, read-write)

### 🧠 AI-Powered
- Auto-ingest documents into wiki
- Semantic querying
- Wiki quality auditing
- Graph-based knowledge visualization

### 📊 Database
- SQLite for development (included)
- PostgreSQL ready for production
- Automatic schema management
- Relationship integrity

---

## Common Tasks

### Register a New User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secure"}'
```

### Create a Wiki Project
```bash
# Get token from login first
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Research Wiki","description":"My research notes"}'
```

### Share a Project
```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","permission_level":"read_write"}'
```

### Upload and Ingest a Document
```bash
# Upload
curl -X POST http://localhost:8000/api/projects/{project_id}/files/raw/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# Ingest
curl -X POST http://localhost:8000/api/projects/{project_id}/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"document.pdf"}'
```

### Query the Wiki
```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is machine learning?"}'
```

---

## Troubleshooting

### "Database locked" error
- Ensure only one server instance is running
- Close any open database connections

### "Invalid token" error
- Token may have expired (30 minute expiration)
- Re-login to get a new token

### "Access denied" (403) error
- You don't own the project
- You're not a member of the shared project
- Your membership permission is insufficient

### "API Key not configured"
- Check `.env` file has `GEMINI_API_KEY` set
- API key must be valid and have quota

---

## Frontend Update Checklist

Your existing frontend needs updates to work with the new system:

- [ ] Add login/registration forms
- [ ] Store JWT token in localStorage
- [ ] Add Authorization header to all API requests
- [ ] Update API URLs to include `project_id`
- [ ] Add project selector/dashboard
- [ ] Add project sharing UI
- [ ] Handle 403 errors for permission denied
- [ ] Show permission levels in UI

---

## Performance Notes

- **SQLite**: Suitable for single-server, moderate load
- **Scale**: For 100+ projects, consider PostgreSQL
- **Query Time**: Full-text search across all pages takes 1-2 seconds
- **Database Size**: ~10KB per small project (varies with content)

---

## Deployment

### Development
```bash
python server.py
```

### Production (Docker - optional)
```bash
docker build -t llmwiki .
docker run -p 8000:8000 -e GEMINI_API_KEY=sk-... llmwiki
```

### Production (Manual)
1. Set `SECRET_KEY` to a strong random value
2. Switch to PostgreSQL if needed
3. Configure HTTPS with nginx/gunicorn
4. Set up automated backups
5. Enable monitoring and logging

---

## Support & Resources

- **Google Generative AI**: https://ai.google.dev/
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **JWT**: https://jwt.io/

---

## License

This project is provided as-is. Use and modify freely.

---

## What's Next?

1. **Test the backend** - Run `python client_example.py --demo`
2. **Update the frontend** - Add auth UI and project management
3. **Test end-to-end** - Register, create projects, share, ingest, query
4. **Deploy** - Set up production environment
5. **Extend** - Add custom features as needed

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           Frontend (HTML/CSS/JS)                │
│  [TODO: Add Auth UI, Project Management UI]    │
└─────────────┬───────────────────────────────────┘
              │
              │ HTTP/JSON (Authenticated Requests)
              │
┌─────────────▼───────────────────────────────────┐
│      FastAPI Server (server.py)                 │
│  ┌─────────────────────────────────────┐        │
│  │ Auth Endpoints (JWT Tokens)         │        │
│  │ Project Management                  │        │
│  │ Wiki Operations                     │        │
│  │ AI Operations (Ingest/Query/Lint)   │        │
│  └─────────────────────────────────────┘        │
└─────────────┬───────────────────────────────────┘
              │
              │ SQL
              │
┌─────────────▼───────────────────────────────────┐
│    SQLite Database (llmwiki.db)                 │
│  ┌─────────────────────────────────────┐        │
│  │ Users                               │        │
│  │ Projects (owned & shared)           │        │
│  │ ProjectMemberships                  │        │
│  │ WikiPages (project-scoped)          │        │
│  │ RawDocuments (project-scoped)       │        │
│  └─────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘

              │
              │ API Calls
              │
┌─────────────▼───────────────────────────────────┐
│    Google Generative AI (Gemini)                │
│  - Ingest (parse & organize documents)          │
│  - Query (semantic search & answering)          │
│  - Lint (quality audits)                        │
└─────────────────────────────────────────────────┘
```

---

**Version**: 2.0 (Multi-Project Edition)  
**Status**: Backend Complete ✅ | Frontend Updates Needed ⏳  
**Last Updated**: 2024-06-19
