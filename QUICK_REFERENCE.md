# ⚡ LLMwiki Quick Reference Card

Keep this handy while using LLMwiki!

---

## 🚀 Quick Start Commands

### Docker (Recommended)
```bash
# 1. Setup
cp .env.example .env
nano .env  # Add GEMINI_API_KEY

# 2. Start
docker-compose up -d

# 3. Access
open http://localhost:8000

# 4. Logs
docker-compose logs -f

# 5. Stop
docker-compose down
```

### Python Native
```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add GEMINI_API_KEY

# 2. Start
python server.py

# 3. Access
open http://localhost:8000
```

---

## 🔑 Essential Configuration

### .env File
```env
GEMINI_API_KEY=your-api-key-here
SECRET_KEY=random-32-character-string
DATABASE_URL=sqlite:///./llmwiki.db
```

### Generate Strong SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastAPI backend |
| `database.py` | Database models |
| `auth.py` | Authentication |
| `agent.py` | AI operations |
| `index.html` | Frontend interface |
| `app.js` | Frontend logic |
| `llmwiki.db` | Data storage |
| `.env` | Configuration |

---

## 🔌 API Quick Reference

### Auth (Public)
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@test.com","password":"pass"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

### Projects (Authenticated)
```bash
# Set token
export TOKEN="your_token_here"

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Wiki","description":"Test"}'

# List projects
curl -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN"

# Get project
curl -X GET http://localhost:8000/api/projects/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Files (Project-Scoped)
```bash
# Upload document
curl -X POST http://localhost:8000/api/projects/1/files/raw/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# List raw files
curl -X GET http://localhost:8000/api/projects/1/files/raw \
  -H "Authorization: Bearer $TOKEN"

# List wiki pages
curl -X GET http://localhost:8000/api/projects/1/files/wiki \
  -H "Authorization: Bearer $TOKEN"

# Get wiki page
curl -X GET http://localhost:8000/api/projects/1/files/wiki/filename.md \
  -H "Authorization: Bearer $TOKEN"
```

### Operations
```bash
# Ingest document
curl -X POST http://localhost:8000/api/projects/1/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"doc.pdf"}'

# Query wiki
curl -X POST http://localhost:8000/api/projects/1/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the main topic?"}'
```

---

## 🐳 Docker Commands

### Management
```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Start services
docker-compose start

# Remove services
docker-compose down

# Remove with volumes
docker-compose down -v
```

### Debugging
```bash
# Shell into container
docker-compose exec llmwiki bash

# Check database
docker exec llmwiki sqlite3 /app/llmwiki.db ".tables"

# View specific logs
docker logs llmwiki -f --tail 100

# Check health
docker inspect llmwiki | grep -A 5 Health
```

---

## 🗄️ Database Management

### View Data
```bash
# Connect to database
sqlite3 llmwiki.db

# Show tables
.tables

# Count users
SELECT COUNT(*) FROM users;

# Count projects
SELECT COUNT(*) FROM projects;

# List all projects
SELECT id, name, owner_id FROM projects;

# Exit
.quit
```

### Backup & Restore
```bash
# Backup
cp llmwiki.db llmwiki.db.backup

# Restore
cp llmwiki.db.backup llmwiki.db

# Reload
docker-compose restart llmwiki
```

---

## 🔒 Security Quick Tips

- ✅ Never commit `.env` file to git
- ✅ Add `.env` to `.gitignore`
- ✅ Use strong `SECRET_KEY` (32+ chars)
- ✅ Keep `GEMINI_API_KEY` secret
- ✅ Use HTTPS in production
- ✅ Enable CORS selectively
- ✅ Rotate secrets regularly
- ✅ Monitor access logs

---

## 🐛 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Port 8000 in use | Change port in docker-compose.yml |
| API key error | Check .env has GEMINI_API_KEY set |
| Container won't start | Run `docker-compose logs` to see error |
| Database locked | Stop all instances, restart |
| Permission denied | Check file permissions: `chmod 644 llmwiki.db` |
| Token expired | Login again to get new token |

---

## 📚 Documentation Quick Links

- **QUICKSTART.md** - 5-minute setup
- **INSTALL.md** - Full installation
- **DOCKER_GUIDE.md** - Docker setup
- **API_REFERENCE.md** - All endpoints
- **README_NEW.md** - Architecture
- **DEPLOYMENT_CHECKLIST.md** - Launch checklist

---

## 🎯 Common Workflows

### Create and Manage Project
```
1. Login to http://localhost:8000
2. Click "New Project"
3. Enter name and description
4. Click "Create Project"
5. Now you're in the project
```

### Upload and Ingest Document
```
1. Click "Add" in RAW SOURCES panel
2. Select PDF, TXT, or MD file
3. File uploads to your project
4. Click file in list
5. Click "Compile Into Wiki"
6. New wiki pages created
```

### Query Your Wiki
```
1. Click "Query" tab in right panel
2. Type your question
3. Click "Submit" or press Enter
4. See AI-generated answer
5. Optionally "Save as Page"
```

### Share Project with Team
```
1. Click "Share Project" button
2. Enter team member email
3. Select permission level
4. Click "Share"
5. Team member gets access
```

---

## 🔐 User Roles

### Owner
- Create/delete project
- Upload files
- Edit/delete pages
- Share with others
- Manage members

### Read-Write
- Upload files
- Edit/create pages
- Query wiki
- No delete/share

### Read-Only
- View files/pages
- Query wiki
- No upload/edit/delete

---

## ⏱️ Performance Baseline

- Login: < 100ms
- Create project: < 50ms
- List projects: < 50ms
- Upload document: < 5 seconds
- Ingest (5MB PDF): 10-30 seconds
- Query wiki: 5-15 seconds
- Graph generation: < 10 seconds

---

## 📊 Resource Usage

**Typical Usage:**
- Memory: 300 MB
- CPU: < 20%
- Disk: 100 MB base + data

**During Heavy Operations:**
- Memory: 1-2 GB
- CPU: 50-80%
- Disk: varies with docs

---

## 🚀 Deployment Checklist (Short Version)

- [ ] .env configured with secrets
- [ ] Docker image builds: `docker build -t llmwiki .`
- [ ] Container starts: `docker-compose up -d`
- [ ] API responds: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: http://localhost:8000
- [ ] Can register account
- [ ] Can create project
- [ ] Can upload file
- [ ] Database persists

---

## 🔑 API Key from Gemini

1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create new project
4. Generate API key
5. Copy to `.env` file

---

## 📞 Quick Help

| Need | Read |
|------|------|
| Fast setup | QUICKSTART.md |
| Full install | INSTALL.md |
| Docker help | DOCKER_GUIDE.md |
| API details | API_REFERENCE.md |
| System design | README_NEW.md |
| Deployment | DEPLOYMENT_CHECKLIST.md |

---

## 🎉 First 10 Minutes

```
0:00 - Copy .env.example to .env
1:00 - Add Gemini API key to .env  
2:00 - docker-compose up -d
3:00 - Open http://localhost:8000
4:00 - Register account
5:00 - Create project "My Wiki"
6:00 - Get API key from settings
7:00 - Upload a PDF
8:00 - Click "Compile Into Wiki"
9:00 - See new wiki pages!
10:00 - Try querying your wiki
```

---

**Bookmark this! You'll reference it often. 🚀**
