# 🚀 LLMwiki - Complete Installation & Deployment Guide

> A multi-user, multi-project wiki platform powered by AI, now containerized with Docker

## ⭐ What's New

### Recent Updates (Current Release)

✅ **Authentication System**
- User registration and login
- JWT token-based security
- Logout functionality
- Session persistence

✅ **Multi-Project Support**
- Create unlimited projects
- Switch between projects
- Project-scoped wikis and files
- User-specific project access

✅ **Team Collaboration**
- Share projects with team members
- Permission levels (read-only, read-write)
- View project members
- Manage access controls

✅ **Docker Deployment**
- Production-ready Dockerfile
- docker-compose configuration
- One-command startup
- Database persistence

---

## 🎯 Quick Links

- **Getting Started**: See [QUICKSTART.md](QUICKSTART.md) (5 minutes)
- **Docker Guide**: See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) (comprehensive)
- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md) (all endpoints)
- **Architecture**: See [README_NEW.md](README_NEW.md) (technical overview)

---

## ⚡ Start in 2 Minutes

### Windows
```powershell
# 1. Copy environment template
Copy-Item .env.example .env

# 2. Edit .env with your Gemini API key
notepad .env

# 3. Start application
docker-compose up -d

# 4. Open browser
start http://localhost:8000
```

### macOS/Linux
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your Gemini API key
nano .env

# 3. Start application
docker-compose up -d

# 4. Open browser
open http://localhost:8000
```

---

## 📋 System Requirements

### Minimum
- Docker & Docker Compose (for containerized deployment)
- OR Python 3.9+ (for native deployment)
- 2 GB RAM
- 500 MB disk space

### Recommended (Production)
- Docker & Docker Compose
- PostgreSQL database
- 4 GB RAM
- 10 GB disk space
- HTTPS certificate (Let's Encrypt)

---

## 🔑 Prerequisites

### 1. Get Gemini API Key (Free)
1. Go to: https://ai.google.dev/
2. Click "Get API Key"
3. Follow setup wizard
4. Copy your API key

### 2. Install Docker (Optional but Recommended)
- **Windows**: https://www.docker.com/products/docker-desktop
- **macOS**: https://www.docker.com/products/docker-desktop
- **Linux**: `curl -fsSL https://get.docker.com | sh`

### 3. Clone/Prepare Project
```bash
cd llmwiki
cp .env.example .env
# Edit .env with your API key
```

---

## 🚀 Installation Methods

### Method 1: Docker Compose (Recommended)

**Pros**: One command, no Python setup, reproducible environment
**Cons**: Requires Docker

```bash
# Setup
cp .env.example .env
nano .env  # Add your Gemini API key

# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Access at: **http://localhost:8000**

### Method 2: Docker CLI

**Pros**: Direct Docker control
**Cons**: Manual command line

```bash
# Build image
docker build -t llmwiki:latest .

# Run container
docker run -d \
  --name llmwiki \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your-key-here" \
  -e SECRET_KEY="your-secret-key" \
  -v $(pwd)/llmwiki.db:/app/llmwiki.db \
  llmwiki:latest

# View logs
docker logs -f llmwiki

# Stop
docker stop llmwiki
```

### Method 3: Native Python

**Pros**: Direct control, easier debugging
**Cons**: Requires Python setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Add your Gemini API key

# Run server
python server.py
```

Access at: **http://localhost:8000**

---

## 🎯 First Time Usage

### 1️⃣ Register Account
- Click "Create one" on login screen
- Enter username, email, password
- Click "Create Account"

### 2️⃣ Login
- Enter credentials
- Click "Sign In"

### 3️⃣ Create Project
- Click "New Project"
- Name: "My First Wiki"
- Description: "Testing LLMwiki"
- Click "Create Project"

### 4️⃣ Configure API
- Click settings icon (⚙️) top right
- Paste Gemini API Key
- Click "Save Configuration"

### 5️⃣ Upload Document
- Click "Add" in RAW SOURCES
- Select PDF, TXT, or MD file
- File uploads to project

### 6️⃣ Create Wiki
- Select uploaded file
- Click "Compile Into Wiki"
- New pages appear in COMPOUNDING WIKI

### 7️⃣ Query Wiki
- Click "Query" tab
- Ask questions about documents
- Agent synthesizes answers

### 8️⃣ Share Project
- Click "Share Project"
- Enter team member email
- Set permission level
- Team member gets access

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│   Frontend (HTML/CSS/JavaScript)│
│   - Login/Registration          │
│   - Project Management          │
│   - Wiki Editor                 │
│   - Graph Visualization         │
└────────────┬────────────────────┘
             │ HTTP/JSON (JWT Auth)
             │
┌────────────▼────────────────────┐
│   FastAPI Server                │
│   - Authentication (JWT)        │
│   - Project Management          │
│   - Wiki Operations             │
│   - AI Integration (Gemini)     │
│   - 22 REST API Endpoints       │
└────────────┬────────────────────┘
             │ SQL
┌────────────▼────────────────────┐
│   SQLite Database               │
│   - Users & Authentication      │
│   - Projects & Memberships      │
│   - Wiki Pages & Documents      │
└─────────────────────────────────┘
```

---

## 📁 Project Structure

```
llmwiki/
├── Core Application
│   ├── server.py              # FastAPI application (22 endpoints)
│   ├── database.py            # SQLAlchemy models & ORM
│   ├── auth.py                # JWT authentication
│   ├── agent.py               # AI operations (Gemini)
│
├── Frontend
│   ├── index.html             # Web interface
│   ├── app.js                 # JavaScript logic
│   ├── styles.css             # Styling
│
├── Docker
│   ├── Dockerfile             # Container definition
│   ├── docker-compose.yml     # Multi-container setup
│   ├── .dockerignore          # Build optimization
│
├── Configuration
│   ├── .env.example           # Template (commit this)
│   ├── .env                   # Secrets (don't commit)
│   ├── requirements.txt       # Python dependencies
│
├── Data
│   ├── llmwiki.db            # SQLite database
│   ├── wiki/                 # Wiki markdown files
│   ├── raw/                  # Raw documents
│
└── Documentation
    ├── README.md              # Original documentation
    ├── README_NEW.md          # Updated overview
    ├── QUICKSTART.md          # 5-minute setup
    ├── DOCKER_GUIDE.md        # Docker complete guide
    ├── API_REFERENCE.md       # API endpoints
    ├── SQLITE_MIGRATION.md    # Database schema
    └── CHANGES.md             # What's changed
```

---

## 🔌 API Endpoints (Summary)

### Authentication (Public)
```
POST   /api/auth/register    Create account
POST   /api/auth/login       Get JWT token
GET    /api/auth/me          Current user info
```

### Projects
```
POST   /api/projects              Create project
GET    /api/projects              List projects
GET    /api/projects/{id}         Get project
PUT    /api/projects/{id}         Update project
DELETE /api/projects/{id}         Delete project
POST   /api/projects/{id}/share   Share with user
POST   /api/projects/{id}/unshare Remove user
```

### Wiki (Project-Scoped)
```
GET    /api/projects/{id}/files/wiki              List pages
GET    /api/projects/{id}/files/wiki/{filename}   Read page
POST   /api/projects/{id}/files/wiki/{filename}   Create/update page
POST   /api/projects/{id}/ingest                  Ingest document
POST   /api/projects/{id}/query                   Query wiki
POST   /api/projects/{id}/query/save              Save answer as page
POST   /api/projects/{id}/lint                    Audit wiki
GET    /api/projects/{id}/graph                   Knowledge graph
```

### Files (Project-Scoped)
```
GET    /api/projects/{id}/files/raw           List documents
POST   /api/projects/{id}/files/raw/upload    Upload file
```

### Configuration
```
GET    /api/projects/{id}/config    Get config
POST   /api/projects/{id}/config    Save config
```

**See [API_REFERENCE.md](API_REFERENCE.md) for detailed documentation**

---

## 🔐 Security

### Best Practices
- ✅ JWT token authentication
- ✅ Password hashing (bcrypt)
- ✅ Project-scoped access control
- ✅ Permission levels (read/write)
- ✅ Non-root Docker user

### For Production
1. Change `SECRET_KEY` in .env:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Use HTTPS:
   ```bash
   docker run -p 443:8000 ...
   ```

3. Use PostgreSQL instead of SQLite:
   ```yaml
   DATABASE_URL=postgresql://user:pass@host/db
   ```

4. Setup reverse proxy (nginx):
   - SSL termination
   - Rate limiting
   - Access logging

---

## 🧪 Testing

### Quick Test (curl)
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@test.com","password":"pass"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Save token
export TOKEN="<access_token_from_response>"

# Get current user
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Full Test (Python)
```python
from client_example import LLMWikiClient

client = LLMWikiClient("http://localhost:8000")

# Register
client.register("user", "user@test.com", "pass")

# Login
client.login("user", "pass")

# Create project
proj = client.create_project("Test", "Testing")

# List projects
projects = client.list_projects()
print(projects)
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Change port in `docker-compose.yml` or `server.py` |
| Database locked | Stop all instances, restart |
| API key error | Check `.env` file, verify key at https://ai.google.dev/ |
| Token expired | Login again to get new token |
| Docker won't start | Check logs: `docker logs llmwiki` |
| Permission denied | Check file permissions: `chmod 777 llmwiki.db` |

**More help**: See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for complete troubleshooting

---

## 📊 Database Management

### View Database
```bash
sqlite3 llmwiki.db

# Inside sqlite3 prompt:
.tables
SELECT * FROM users;
SELECT * FROM projects;
.quit
```

### Backup
```bash
# Stop server
docker-compose down

# Backup database
cp llmwiki.db llmwiki.db.backup

# Restart
docker-compose up -d
```

### Reset (⚠️ Deletes all data)
```bash
rm llmwiki.db
docker-compose restart
```

---

## 🚀 Production Deployment

### AWS ECS
```bash
# Push image to ECR
aws ecr create-repository --repository-name llmwiki
docker tag llmwiki:latest <account>.dkr.ecr.<region>.amazonaws.com/llmwiki:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/llmwiki:latest

# Deploy with CloudFormation or ECS console
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/<project>/llmwiki
gcloud run deploy llmwiki --image gcr.io/<project>/llmwiki \
  --platform managed \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=<key>,SECRET_KEY=<secret>
```

### Azure Container Instances
```bash
az acr build --registry <registry> --image llmwiki:latest .
az container create --resource-group <group> \
  --name llmwiki \
  --image <registry>.azurecr.io/llmwiki:latest \
  --ports 8000 \
  --environment-variables GEMINI_API_KEY=<key>
```

### Kubernetes
```bash
# Create secret
kubectl create secret generic llmwiki-secrets \
  --from-literal=GEMINI_API_KEY=<key> \
  --from-literal=SECRET_KEY=<secret>

# Deploy
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llmwiki
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llmwiki
  template:
    metadata:
      labels:
        app: llmwiki
    spec:
      containers:
      - name: llmwiki
        image: llmwiki:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: llmwiki-secrets
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"
EOF
```

---

## 📈 Performance Optimization

### For Small Teams (< 10 users)
- SQLite database (default)
- Single server instance
- Docker Compose on modest hardware
- Basic monitoring

### For Growing Teams (10-100 users)
- PostgreSQL database
- Load balancer (nginx)
- Multiple server instances
- Monitoring + alerting
- Automated backups

### For Enterprise (100+ users)
- PostgreSQL + replication
- Kubernetes orchestration
- CDN for static assets
- Advanced monitoring (Prometheus, Grafana)
- High availability setup

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Comprehensive Docker instructions |
| [API_REFERENCE.md](API_REFERENCE.md) | All API endpoints with examples |
| [README_NEW.md](README_NEW.md) | Technical architecture overview |
| [SQLITE_MIGRATION.md](SQLITE_MIGRATION.md) | Database schema & setup |
| [CHANGES.md](CHANGES.md) | Detailed changelog |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | Feature status tracking |

---

## ❓ FAQ

**Q: Can I use PostgreSQL?**
A: Yes! See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for PostgreSQL setup

**Q: How do I backup my data?**
A: Copy llmwiki.db file or use docker volume commands

**Q: Is it secure?**
A: Uses JWT auth, bcrypt passwords, and project-scoped access control

**Q: Can I run multiple instances?**
A: Yes with PostgreSQL backend. SQLite doesn't support concurrent writes.

**Q: How do I update to new versions?**
A: Pull latest code, rebuild image, restart containers

**Q: Can I self-host?**
A: Yes! All code is yours, deploy anywhere Docker runs

---

## 🤝 Contributing

Found an issue? Have a feature idea?
1. Check [CHANGES.md](CHANGES.md) for recent updates
2. Review [API_REFERENCE.md](API_REFERENCE.md) for endpoint docs
3. See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for roadmap

---

## 📞 Support

**Having issues?**
1. Check [DOCKER_GUIDE.md](DOCKER_GUIDE.md) troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Verify environment: Check .env file
4. Test API: Visit http://localhost:8000/docs

**API Issues?**
- See [API_REFERENCE.md](API_REFERENCE.md)
- Check error messages in response body
- Verify JWT token in Authorization header

---

## 📜 License & Terms

This project is provided as-is. See individual documentation files for details.

---

## 🎉 Next Steps

1. ✅ **Install**: Follow installation method above
2. ✅ **Setup**: Run application and register account
3. ✅ **Create**: Make your first project
4. ✅ **Upload**: Add documents
5. ✅ **Explore**: Query your wiki
6. ✅ **Share**: Invite team members
7. ✅ **Deploy**: Take to production with Docker

---

**Happy documenting! 🚀**

Questions? See the [documentation](#-documentation) section above.
