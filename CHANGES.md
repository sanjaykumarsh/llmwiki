# SQLite Migration - Changes Summary

## New Files Created

### 1. `database.py`
- **SQLAlchemy ORM models** for SQLite
- Models: `User`, `Project`, `ProjectMembership`, `WikiPage`, `RawDocument`
- `PermissionLevel` enum for read_only / read_write sharing
- Password hashing utilities using bcrypt
- Database initialization and session management

### 2. `auth.py`
- JWT-based authentication using `python-jose`
- User registration and login logic
- `get_current_user()` dependency for FastAPI
- Token creation and validation
- Pydantic schemas: `UserSchema`, `UserRegisterSchema`, `UserLoginSchema`, `TokenSchema`

### 3. `SQLITE_MIGRATION.md`
- Comprehensive migration guide
- Architecture overview
- New endpoint documentation
- Usage examples and workflows
- Permission levels explanation
- Troubleshooting guide

### 4. `client_example.py`
- Python client library demonstrating API usage
- Example workflows (register, create project, upload, ingest, query, share)
- Interactive CLI for testing endpoints

### 5. `llmwiki.db`
- SQLite database file (auto-created on first run)
- Stores all users, projects, wiki pages, and raw documents

---

## Files Modified

### 1. `requirements.txt`
**Added dependencies:**
- `sqlalchemy` - ORM for database
- `passlib[bcrypt]` - Password hashing
- `python-jose[cryptography]` - JWT tokens
- `pyjwt` - Additional JWT utilities

### 2. `server.py` (Complete Refactoring)
**Major changes:**

#### Imports
- Added: SQLAlchemy, database models, auth utilities

#### Startup Event
- Added `@app.on_event("startup")` to initialize database
- Auto-create tables on first run

#### New Pydantic Schemas
- `ProjectCreateRequest`, `ProjectUpdateRequest`, `ProjectShareRequest`, `ProjectSchema`
- Updated request schemas to include `project_id`

#### New Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

#### New Project Management Endpoints
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects (owned + shared)
- `GET /api/projects/{project_id}` - Get project details
- `PUT /api/projects/{project_id}` - Update project
- `DELETE /api/projects/{project_id}` - Delete project
- `POST /api/projects/{project_id}/share` - Share project
- `DELETE /api/projects/{project_id}/share/{username}` - Unshare project

#### Updated Endpoints (Now Project-Scoped)
All existing endpoints now include `project_id` in URL and require authentication:
- `GET /api/projects/{project_id}/files/raw`
- `POST /api/projects/{project_id}/files/raw/upload`
- `GET /api/projects/{project_id}/files/wiki`
- `GET /api/projects/{project_id}/files/wiki/{filename}`
- `POST /api/projects/{project_id}/files/wiki/{filename}`
- `GET /api/projects/{project_id}/graph`
- `POST /api/projects/{project_id}/ingest`
- `POST /api/projects/{project_id}/query`
- `POST /api/projects/{project_id}/query/save`
- `POST /api/projects/{project_id}/lint`

#### Helper Function
- `check_project_access()` - Validates user access to project and permission level

#### Backward Compatibility
- Config endpoints unchanged (no authentication required)
- Static file serving unchanged

### 3. `agent.py` (Extended, Not Replaced)
**Added new database-compatible functions:**
- `run_ingest_from_content()` - Ingests raw document content from database
- `run_query_from_pages()` - Queries wiki pages from database objects
- `run_lint_from_pages()` - Lints wiki pages from database objects

**Old functions preserved** for backward compatibility:
- `run_ingest()` - Original file-based version
- `run_query()` - Original file-based version
- `run_lint()` - Original file-based version

---

## Key Architectural Changes

### Before (File-Based)
```
single-project
└── wiki/ (shared directory)
    └── *.md files
└── raw/ (shared directory)
    └── source files
```

### After (SQLite Multi-Project)
```
multi-user
├── User 1
│   ├── Project A (owned)
│   │   ├── wiki_pages
│   │   └── raw_documents
│   └── Project B (shared, read_write)
└── User 2
    ├── Project B (owned)
    ├── Project C (shared, read_only)
    └── Project A (shared, read_only)
```

---

## Security Improvements

1. **Authentication** - All wiki operations require JWT token
2. **Authorization** - Project-level access control
3. **Permission Levels** - Granular read_only / read_write permissions
4. **Password Hashing** - bcrypt hashing of passwords
5. **Token Expiration** - JWT tokens expire after 30 minutes (configurable)
6. **Database Isolation** - Projects are fully isolated by project_id foreign keys

---

## Data Migration Path

Existing wiki and raw files are NOT automatically migrated. To preserve data:

1. **Keep old files** in `raw/` and `wiki/` directories
2. **Create new projects** via API for each wiki you want to migrate
3. **Re-ingest files** using the new endpoints
4. **Review and recreate** existing wiki pages as needed

This approach ensures:
- No data loss
- Ability to restructure as needed
- Opportunity to organize projects logically
- Clean separation between old and new system

---

## Testing the Changes

### 1. Start the server
```bash
python server.py
```

### 2. Test with client example
```bash
python client_example.py --demo
```

Or interactive:
```bash
python client_example.py
> register demo demo@example.com password123
> create-project My Wiki
> list-projects
```

### 3. Use curl for API testing
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","email":"user1@test.com","password":"pass123"}'

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name":"My Project","description":"Test"}'
```

---

## Deployment Considerations

### Development
- Use default `SECRET_KEY` (change for production!)
- SQLite is fine for testing

### Production
1. **Change SECRET_KEY** in environment
2. **Use PostgreSQL** instead of SQLite (for multi-server scenarios)
   - Update: `DATABASE_URL = "postgresql://user:pass@host/db"`
   - Install: `pip install psycopg2-binary`
3. **Enable HTTPS** and set secure headers
4. **Add rate limiting** for auth endpoints
5. **Set up database backups**
6. **Use environment variables** for sensitive data

---

## Breaking Changes

⚠️ **Important for existing deployments:**

1. All wiki endpoints now require `project_id` in URL
2. All wiki operations require authentication
3. Old `.env` format still supported (GEMINI_API_KEY)
4. File-based wiki/raw storage NOT automatically migrated

### Example URL Changes
- `/api/files/wiki` → `/api/projects/{project_id}/files/wiki`
- `/api/files/raw` → `/api/projects/{project_id}/files/raw`
- `/api/ingest` → `/api/projects/{project_id}/ingest`

---

## Frontend Updates Required

Your JavaScript frontend needs updates:

1. **Add auth UI** (login/register forms)
2. **Add project selection** (dropdown/list)
3. **Update API calls** to include Authorization header
4. **Update URLs** with project_id
5. **Store JWT token** in localStorage

Example:
```javascript
// Store token after login
localStorage.setItem('token', response.access_token);

// Use in all requests
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json'
};

// Update API URLs
const projectId = selectedProject.id;
const response = await fetch(`/api/projects/${projectId}/files/wiki`, { headers });
```

---

## Configuration

### Environment Variables (.env)
```env
GEMINI_API_KEY=sk-...
SECRET_KEY=your-secret-key
```

### Python Configuration (auth.py)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token lifetime (default: 30)
- `ALGORITHM` - JWT algorithm (default: HS256)

### Database Configuration (database.py)
- `DATABASE_URL` - Connection string (default: SQLite at root)

---

## Performance Notes

- SQLite is suitable for single-server deployments with moderate load
- For scale, migrate to PostgreSQL
- Added indexes on: `users.username`, `users.email`, `projects.owner_id`
- WikiPage queries are project-scoped for efficiency

---

## Next Steps for Teams

1. ✅ **Backend migration complete**
2. ⏳ **Frontend refactoring needed** (auth UI, project management)
3. ⏳ **E2E testing** (register, create projects, share, query)
4. ⏳ **Data migration** (optional: preserve old wiki content)
5. ⏳ **Deployment** (set SECRET_KEY, use PostgreSQL if needed)

---

## Rollback Plan (if needed)

The old file-based endpoints and logic are preserved:
- `run_ingest()`, `run_query()`, `run_lint()` in `agent.py` still work
- Raw and wiki files remain in `raw/` and `wiki/` directories
- Remove `database.py` and `auth.py` imports from `server.py`
- Restore old endpoint definitions from git history

However, it's recommended to proceed with the new system rather than rollback.
