# LLMwiki - Full Stack Setup & Deployment Guide

## ⚡ Quick Start (5 Minutes)

### For Windows (Using Docker Desktop)

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Prepare Environment**
   ```powershell
   cd llmwiki
   
   # Copy example env file
   Copy-Item .env.example .env
   
   # Edit .env with your Gemini API key
   notepad .env
   ```

3. **Start the Application**
   ```powershell
   # Build and start services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

4. **Access the App**
   - Open browser: http://localhost:8000
   - Register account
   - Create first project
   - Configure Gemini API key
   - Start using!

5. **Stop the App**
   ```powershell
   docker-compose down
   ```

### For macOS/Linux

Replace `Copy-Item` with `cp` in step 2, rest is the same.

---

## 📋 Full Setup Instructions

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional, for containerized deployment)
- Google Gemini API key (free tier available at https://ai.google.dev/)

### Option 1: Direct Python Installation (Development)

```bash
# Clone/navigate to project
cd llmwiki

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your Gemini API key
nano .env  # or use your editor

# Run server
python server.py
```

Access at: http://localhost:8000

### Option 2: Docker (Recommended)

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for complete Docker instructions.

Quick start:
```bash
# Copy environment file
cp .env.example .env
# Edit with your API key
nano .env

# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🔑 Getting Your API Key

1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new project or select existing
4. Generate API key
5. Copy and paste into `.env` file

---

## 🎯 First Time Usage

### 1. Registration
- Click "Create one" link on login screen
- Enter username, email, password
- Click "Create Account"

### 2. Login
- Use your credentials
- Click "Sign In"

### 3. Create Project
- Click "New Project" button
- Enter project name and description
- Click "Create Project"

### 4. Configure API
- Click settings icon (gear) top right
- Paste your Gemini API Key
- Click "Save Configuration"

### 5. Upload Documents
- Click "Add" button in RAW SOURCES panel
- Select PDF, TXT, or MD files
- Files will upload to your project

### 6. Compile Wiki
- Select a raw document
- Click "Compile Into Wiki"
- Wait for processing
- New wiki pages will appear in COMPOUNDING WIKI panel

### 7. Query Your Wiki
- Click "Query" tab in Wiki Programmer
- Ask questions about your documents
- Agent will search and synthesize answers
- Optionally save answers as new wiki pages

### 8. Explore & Share
- Click "Interactive Graph" tab to see knowledge network
- Click "Share Project" to invite team members
- Set permission levels (read-only or read-write)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────┐
│   Frontend (HTML/CSS/JS)        │
│   - Login/Registration UI       │
│   - Project Management         │
│   - Wiki Reader/Editor         │
│   - Graph Visualization        │
└────────────┬────────────────────┘
             │ HTTP/JSON
             │ (JWT Authenticated)
┌────────────▼────────────────────┐
│   FastAPI Server (server.py)    │
│   - 22 REST API Endpoints      │
│   - Authentication (JWT)       │
│   - Project Management         │
│   - Wiki Operations            │
│   - AI Integration             │
└────────────┬────────────────────┘
             │ SQL
┌────────────▼────────────────────┐
│   SQLite Database               │
│   - Users                       │
│   - Projects                    │
│   - Wiki Pages                  │
│   - Raw Documents              │
└─────────────────────────────────┘
```

---

## 📁 Project Structure

```
llmwiki/
├── server.py              # FastAPI server with endpoints
├── database.py            # SQLAlchemy models
├── auth.py                # JWT authentication
├── agent.py               # AI operations (ingest, query, lint)
├── app.js                 # Frontend JavaScript (auth + projects)
├── index.html             # Frontend HTML (login + app UI)
├── styles.css             # Frontend styles
├── requirements.txt       # Python dependencies
│
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Multi-container setup
├── .dockerignore          # Files to exclude from Docker
│
├── llmwiki.db            # SQLite database (auto-created)
├── wiki/                 # Wiki markdown files
├── raw/                  # Raw documents
│
├── .env.example          # Environment template
├── .env                  # Environment (create from example)
│
└── Documentation/
    ├── README.md         # Main documentation
    ├── README_NEW.md     # Updated project overview
    ├── API_REFERENCE.md  # API endpoint documentation
    ├── DOCKER_GUIDE.md   # Docker setup guide
    ├── SQLITE_MIGRATION.md
    ├── CHANGES.md
    └── IMPLEMENTATION_STATUS.md
```

---

## 🔌 API Endpoints

All endpoints (except auth) require JWT token in header:
```
Authorization: Bearer <your_token>
```

### Authentication (Public)
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/share` - Share with user
- `POST /api/projects/{id}/unshare` - Remove access

### Wiki (Project-Scoped)
- `GET /api/projects/{id}/files/wiki` - List pages
- `GET /api/projects/{id}/files/wiki/{filename}` - Read page
- `POST /api/projects/{id}/files/wiki/{filename}` - Create/update page
- `POST /api/projects/{id}/ingest` - Ingest document
- `POST /api/projects/{id}/query` - Query wiki
- `POST /api/projects/{id}/query/save` - Save query as page
- `POST /api/projects/{id}/lint` - Audit wiki
- `GET /api/projects/{id}/graph` - Get knowledge graph

### Raw Documents (Project-Scoped)
- `GET /api/projects/{id}/files/raw` - List documents
- `POST /api/projects/{id}/files/raw/upload` - Upload file

### Configuration (Project-Scoped)
- `GET /api/projects/{id}/config` - Get config
- `POST /api/projects/{id}/config` - Save config (API key)

---

## 🧪 Testing

### Test with Python Client
```python
from client_example import LLMWikiClient

client = LLMWikiClient("http://localhost:8000")

# Register
client.register("testuser", "test@example.com", "password123")

# Login
client.login("testuser", "password123")

# Create project
project = client.create_project("My Wiki", "Test project")
project_id = project['id']

# Upload document
client.upload_document(project_id, "document.pdf")

# Ingest
client.ingest(project_id, "document.pdf")

# Query
answer = client.query(project_id, "What is in the document?")
print(answer['answer'])
```

### Test with curl
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }' | jq .access_token

# Save token
export TOKEN="<token_from_response>"

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Wiki",
    "description": "Test project"
  }'
```

---

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
# Find process using port
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000

# Change port in server.py or docker-compose.yml
# From: uvicorn.run(..., port=8000)
# To: uvicorn.run(..., port=8001)
```

### Database Locked Error
```bash
# Only one server instance can access SQLite at a time
# Stop all running instances and restart

# Docker:
docker-compose down
docker-compose up -d
```

### API Key Not Configured
- Check your `.env` file has GEMINI_API_KEY set
- Verify API key is valid at https://ai.google.dev/
- Restart server after changing .env

### Token Expired
- Tokens expire after 30 minutes
- Login again to get new token
- Change ACCESS_TOKEN_EXPIRE_MINUTES in server.py if needed

### Docker Permission Issues
```bash
# Fix database file permissions
chmod 777 llmwiki.db

# Rebuild image
docker-compose build --no-cache

# Restart
docker-compose up -d
```

---

## 📊 Database Management

### View Database
```bash
# Using sqlite3 command line
sqlite3 llmwiki.db

# List tables
.tables

# View schema
.schema

# Query data
SELECT * FROM users;
SELECT * FROM projects;
```

### Backup Database
```bash
# Stop server first
docker-compose stop

# Copy database
cp llmwiki.db llmwiki.db.backup

# Restart
docker-compose start
```

### Reset Database
```bash
# WARNING: Deletes all data!
rm llmwiki.db

# Database will be recreated on next run
docker-compose restart
```

---

## 🔒 Security Checklist

- [ ] Changed SECRET_KEY in .env (use `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Set secure GEMINI_API_KEY (never commit to git)
- [ ] Added .env to .gitignore
- [ ] Enabled HTTPS for production (use nginx reverse proxy)
- [ ] Set strong database password if using PostgreSQL
- [ ] Configured CORS appropriately
- [ ] Reviewed and limited file upload sizes
- [ ] Set up automated backups
- [ ] Enabled firewall and restrict access

---

## 📈 Performance Tips

- Use PostgreSQL for production instead of SQLite
- Enable caching for frequently accessed pages
- Set up CDN for static files
- Monitor database query performance
- Use connection pooling for databases
- Consider load balancing for multiple servers

---

## 🚀 Deployment

### To Production Server

1. **Prepare Server**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Deploy Application**
   ```bash
   # Clone repository
   git clone <your-repo-url> llmwiki
   cd llmwiki
   
   # Setup environment
   cp .env.example .env
   nano .env  # Configure production settings
   
   # Start services
   docker-compose up -d
   
   # Setup SSL with nginx (optional but recommended)
   sudo apt install nginx
   # Configure nginx as reverse proxy with SSL
   ```

3. **Monitor**
   ```bash
   # View logs
   docker-compose logs -f
   
   # Check health
   curl http://localhost:8000/api/health
   
   # Monitor resources
   docker stats
   ```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://www.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [JWT Authentication](https://jwt.io/)

---

## ❓ FAQ

**Q: Can I use PostgreSQL instead of SQLite?**
A: Yes! Change DATABASE_URL in .env and uncomment postgres service in docker-compose.yml

**Q: How do I backup my data?**
A: Stop services, copy llmwiki.db file, restart. Or use docker volume commands.

**Q: Can I run multiple instances?**
A: Yes, with PostgreSQL as backend. SQLite doesn't support concurrent writes.

**Q: How do I upgrade?**
A: Pull latest code, update dependencies, restart services.

**Q: Is there an admin dashboard?**
A: Not yet. You can query the database directly using sqlite3.

---

## 💬 Support

For issues, questions, or feature requests:
1. Check the documentation files
2. Review API_REFERENCE.md for endpoint details
3. Check logs: `docker-compose logs`
4. See TROUBLESHOOTING section above

---

**Happy coding! 🚀**
