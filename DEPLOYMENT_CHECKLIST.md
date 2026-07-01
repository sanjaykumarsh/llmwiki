# 🚀 LLMwiki Deployment Checklist

Use this checklist to ensure a smooth deployment, whether local development, staging, or production.

---

## 📋 Pre-Deployment

### Prerequisites Check
- [ ] Docker installed and running (or Python 3.9+ for native)
- [ ] Gemini API key obtained from https://ai.google.dev/
- [ ] 2 GB RAM available
- [ ] 500 MB disk space available
- [ ] Port 8000 not in use (or modified if needed)

### Project Preparation
- [ ] Cloned/downloaded LLMwiki project
- [ ] Read INSTALL.md (this document)
- [ ] Read QUICKSTART.md for your deployment method
- [ ] Database backed up if upgrading existing installation

### Environment Setup
- [ ] `.env.example` exists in project root
- [ ] `.env` created from `.env.example`
- [ ] GEMINI_API_KEY set in `.env`
- [ ] SECRET_KEY set to secure random value in `.env`
- [ ] `.env` file NOT committed to version control
- [ ] .gitignore includes `.env`

---

## 🐳 Docker Deployment Checklist

### Image Building
- [ ] Dockerfile exists in project root
- [ ] .dockerignore exists and optimized
- [ ] Docker build succeeds: `docker build -t llmwiki:latest .`
- [ ] Image size is reasonable (< 500 MB)
- [ ] Image scanning shows no critical vulnerabilities: `docker scan llmwiki:latest`

### Configuration
- [ ] docker-compose.yml exists
- [ ] Volume mounts configured:
  - [ ] llmwiki.db (database persistence)
  - [ ] wiki/ (wiki pages)
  - [ ] raw/ (raw documents)
- [ ] Port mapping correct (8000:8000)
- [ ] Environment variables properly set
- [ ] Health checks configured
- [ ] Resource limits set (optional but recommended)

### Container Deployment
- [ ] Container builds without errors: `docker-compose build`
- [ ] Container starts: `docker-compose up -d`
- [ ] Container stays running: `docker-compose ps`
- [ ] Logs are clean: `docker-compose logs`
- [ ] Health check passes: `docker inspect llmwiki` shows healthy
- [ ] Port 8000 accessible locally

### Testing Container
- [ ] API responds: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: Browser shows login screen at http://localhost:8000
- [ ] Database created: `docker exec llmwiki ls -la /app/llmwiki.db`
- [ ] No permission errors in logs
- [ ] Network connectivity works

---

## 🔐 Security Checklist

### Secrets Management
- [ ] SECRET_KEY is strong (32+ characters)
- [ ] GEMINI_API_KEY is valid and not shared
- [ ] .env file is NOT in version control
- [ ] No secrets in Dockerfile or docker-compose.yml
- [ ] Environment variables used for all sensitive data
- [ ] Docker secrets used if available (Swarm/K8s)

### Authentication
- [ ] JWT token validation working
- [ ] Password hashing enabled (bcrypt)
- [ ] Token expiration set (30 minutes default)
- [ ] Logout functionality works
- [ ] Expired tokens trigger re-login

### Access Control
- [ ] Project-scoped file access enforced
- [ ] Permission levels working (read-only, read-write)
- [ ] User cannot access other users' projects
- [ ] Share/unshare functionality secure
- [ ] Admin operations restricted properly

### Network Security
- [ ] HTTPS not required for local (but check firewall)
- [ ] CORS settings appropriate for deployment environment
- [ ] API rate limiting configured (recommended)
- [ ] File upload size limits enforced
- [ ] SQL injection prevention (SQLAlchemy ORM)

### Data Protection
- [ ] Database file permissions restricted (600 or 644)
- [ ] Backups encrypted if stored remotely
- [ ] Sensitive logs not exposed
- [ ] User passwords never logged
- [ ] API keys never logged

---

## 🌐 Network & Infrastructure Checklist

### Local Development
- [ ] Localhost:8000 accessible
- [ ] No port conflicts
- [ ] Firewall allows connections
- [ ] DNS working (if using hostname)

### Staging Environment
- [ ] All above checks plus:
- [ ] SSL certificate configured (self-signed OK)
- [ ] Database accessible
- [ ] File paths writable
- [ ] Logs writable
- [ ] Backups tested

### Production Environment
- [ ] Load balancer configured (nginx/HAProxy)
- [ ] SSL certificate from Let's Encrypt or CA
- [ ] DNS properly configured
- [ ] CDN configured for static files (optional)
- [ ] Monitoring/alerting configured
- [ ] Log aggregation configured
- [ ] Backup/restore tested
- [ ] Disaster recovery plan documented
- [ ] High availability setup (if needed)

---

## 💾 Database Checklist

### SQLite (Development/Small Teams)
- [ ] Database file created: `llmwiki.db`
- [ ] File is readable/writable
- [ ] Volume mounted for persistence
- [ ] Backup strategy in place
- [ ] `sqlite3 llmwiki.db ".tables"` shows all tables

### PostgreSQL (Production)
- [ ] PostgreSQL service running
- [ ] Database created: `llmwiki`
- [ ] User created with correct permissions
- [ ] Connection string in DATABASE_URL
- [ ] Backup schedule configured
- [ ] `psql` connection test succeeds
- [ ] Connection pooling configured (PgBouncer)

### Database Initialization
- [ ] All 5 tables created:
  - [ ] users
  - [ ] projects
  - [ ] project_memberships
  - [ ] wiki_pages
  - [ ] raw_documents
- [ ] Indexes created
- [ ] Foreign keys enforced
- [ ] Cascading deletes working

---

## 🧪 Functionality Testing Checklist

### Authentication
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login fails with wrong password
- [ ] JWT token generated and stored
- [ ] Token included in API requests
- [ ] Token expiration works
- [ ] Logout clears token
- [ ] Expired token triggers re-login

### Projects
- [ ] Create project
- [ ] List shows all user projects
- [ ] Get project details works
- [ ] Update project succeeds
- [ ] Delete project removes all data
- [ ] Projects isolated per user

### Files & Wiki
- [ ] Upload raw document
- [ ] Document appears in raw list
- [ ] Ingest document to wiki
- [ ] Wiki pages created
- [ ] View wiki page renders markdown
- [ ] Edit wiki page works
- [ ] Metadata parsing correct (YAML frontmatter)

### AI Operations
- [ ] Query returns results
- [ ] Lint audit runs
- [ ] Graph visualization generates
- [ ] Save query as wiki page works

### Sharing & Permissions
- [ ] Share project with user
- [ ] Shared user sees project
- [ ] Permission levels enforced
- [ ] Unshare removes access
- [ ] View members shows correct list

### Admin/Config
- [ ] Get config works
- [ ] Set API key works
- [ ] Configuration persists
- [ ] API key used in operations

---

## 📊 Performance Checklist

### Response Times
- [ ] API responses < 200ms (excluding AI ops)
- [ ] Frontend loads < 2 seconds
- [ ] File upload < 5 seconds
- [ ] Ingest operation < 30 seconds

### Resource Usage
- [ ] CPU usage < 50% under normal load
- [ ] Memory usage < 1 GB (normal)
- [ ] Memory usage < 2 GB (Ingest operation)
- [ ] Disk I/O reasonable
- [ ] Database queries optimized

### Load Testing
- [ ] 10 concurrent users
- [ ] 100 concurrent users
- [ ] Large file uploads (100+ MB)
- [ ] Database with 1000+ records

---

## 📈 Monitoring & Logging Checklist

### Logs
- [ ] All errors logged
- [ ] No sensitive data in logs
- [ ] Log level appropriate (info for prod)
- [ ] Log files rotated
- [ ] Log retention policy set

### Monitoring
- [ ] Container health monitored
- [ ] API health endpoint working
- [ ] Database connectivity monitored
- [ ] Disk space monitored
- [ ] Memory usage monitored
- [ ] CPU usage monitored
- [ ] Alerts configured for issues

### Metrics
- [ ] Request count tracked
- [ ] Error rate monitored
- [ ] Response time tracked
- [ ] User count tracked
- [ ] Project count tracked

---

## 🔄 Backup & Recovery Checklist

### Backup Strategy
- [ ] Daily backups scheduled
- [ ] Backups stored off-site
- [ ] Backup retention policy set
- [ ] Backup encryption enabled
- [ ] Backup verification automated

### Recovery Procedures
- [ ] Recovery procedure documented
- [ ] Recovery tested (monthly)
- [ ] Recovery time documented
- [ ] Recovery point objective (RPO) acceptable
- [ ] Recovery time objective (RTO) acceptable

### Data Integrity
- [ ] Database VACUUM/REINDEX scheduled
- [ ] Data integrity checks automated
- [ ] Checksum verification enabled
- [ ] Corruption detection in place

---

## 📚 Documentation Checklist

### Setup Documentation
- [ ] README.md up-to-date
- [ ] INSTALL.md complete
- [ ] QUICKSTART.md verified
- [ ] DOCKER_GUIDE.md comprehensive
- [ ] API_REFERENCE.md current

### Operational Documentation
- [ ] Deployment procedures documented
- [ ] Backup/recovery procedures documented
- [ ] Troubleshooting guide complete
- [ ] Runbook for common issues
- [ ] Escalation procedures defined

### User Documentation
- [ ] User guide written
- [ ] Feature documentation complete
- [ ] API client examples provided
- [ ] FAQ addressed
- [ ] Video tutorials (optional)

---

## 🚀 Pre-Launch Checklist (24 Hours Before)

### Final Verification
- [ ] All tests pass
- [ ] All documentation reviewed
- [ ] Team trained on system
- [ ] Support procedures ready
- [ ] Monitoring alerts active

### Backup Confirmation
- [ ] Fresh backup taken
- [ ] Backup verified
- [ ] Recovery tested
- [ ] Backup location secured
- [ ] Backup team notified

### Communication
- [ ] Stakeholders notified
- [ ] Maintenance window announced
- [ ] Support team briefed
- [ ] Deployment guide reviewed
- [ ] Rollback plan confirmed

---

## 🎯 Launch Day Checklist

### Pre-Launch (2 hours before)
- [ ] Backup completed
- [ ] Monitoring active
- [ ] Support team online
- [ ] Status page updated
- [ ] Runbook accessible

### Launch Phase
- [ ] Build new image
- [ ] Test in staging environment
- [ ] Tag image for production
- [ ] Execute deployment
- [ ] Monitor closely
- [ ] Test all critical features

### Post-Launch (1 hour after)
- [ ] All services healthy
- [ ] Metrics normal
- [ ] No error spikes
- [ ] Users reporting success
- [ ] Logs reviewed
- [ ] Database integrity verified
- [ ] Backups confirmed

### Success Criteria
- [ ] All endpoints responding
- [ ] No critical errors
- [ ] Performance acceptable
- [ ] Users can register/login
- [ ] Projects working
- [ ] Files uploading
- [ ] AI operations functional

---

## 📞 Post-Deployment Support

### First Week
- [ ] Daily health checks
- [ ] User feedback collected
- [ ] Bugs reported and tracked
- [ ] Performance metrics reviewed
- [ ] Security audit conducted

### Ongoing
- [ ] Weekly backups verified
- [ ] Monthly security updates
- [ ] Quarterly performance review
- [ ] Annual disaster recovery test
- [ ] Continuous monitoring

---

## ✅ Sign-Off

**Deployment Owner**: _________________ **Date**: _________

**Verified by**: _________________ **Date**: _________

**Approved by**: _________________ **Date**: _________

---

## 📝 Notes & Issues

Use this section to document any issues encountered:

```
Issue 1:
- Description:
- Resolution:
- Time to fix:

Issue 2:
- Description:
- Resolution:
- Time to fix:
```

---

**Ready to deploy? Start with [QUICKSTART.md](QUICKSTART.md) or [DOCKER_GUIDE.md](DOCKER_GUIDE.md)!**
