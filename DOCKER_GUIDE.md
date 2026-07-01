# Docker and Container Configuration Guide

## Quick Start with Docker Desktop

### 1. Build the Docker Image

```bash
# From the llmwiki project directory
cd llmwiki

# Build the image
docker build -t llmwiki:latest .

# Or use docker-compose (which builds automatically)
docker-compose build
```

### 2. Run with Docker Desktop

#### Option A: Using Docker Compose (Recommended)

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### Option B: Using Docker CLI Directly

```bash
# Run the image
docker run -d \
  --name llmwiki \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your-api-key-here \
  -e SECRET_KEY=your-secret-key \
  -v $(pwd)/llmwiki.db:/app/llmwiki.db \
  llmwiki:latest

# View logs
docker logs -f llmwiki

# Stop container
docker stop llmwiki

# Remove container
docker rm llmwiki
```

### 3. Environment Variables

Create a `.env` file in the project root:

```env
# Required: Google Gemini API Key
GEMINI_API_KEY=AIzaSy_your_actual_api_key_here

# Required: Secret key for JWT tokens (change this in production!)
SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters

# Optional: Database URL (default: SQLite)
# DATABASE_URL=sqlite:///./llmwiki.db
# For PostgreSQL (if using docker-compose with postgres service):
# DATABASE_URL=postgresql://llmwiki:password@postgres:5432/llmwiki

# Optional: Logging level
LOG_LEVEL=info
```

Docker Compose will automatically load this `.env` file.

### 4. Access the Application

Open your browser:
- **Frontend**: http://localhost:8000
- **API**: http://localhost:8000/api/
- **API Docs**: http://localhost:8000/docs (Swagger UI)

### 5. First-Time Setup

1. Register a new account at the login screen
2. Create your first project
3. Configure Gemini API key in settings
4. Upload documents and start compiling your wiki!

## Docker Compose File Explanation

The `docker-compose.yml` includes:

- **llmwiki service**: Main FastAPI application
- **Volume mounts**: 
  - `llmwiki.db`: SQLite database persistence
  - `wiki/`: Wiki pages storage
  - `raw/`: Raw documents storage
- **Port mapping**: 8000:8000 (frontend and API)
- **Health checks**: Automatic container monitoring
- **Restart policy**: Auto-restart if container crashes
- **Resource limits**: CPU and memory constraints (optional)
- **Logging**: Docker JSON logging driver

## Database Options

### SQLite (Default - Development/Testing)
Included by default, no extra setup needed. Database file persists in volume.

```yaml
# In docker-compose.yml
DATABASE_URL=sqlite:///./llmwiki.db
```

### PostgreSQL (Production - Optional)

Uncomment the postgres service in `docker-compose.yml`:

```yaml
postgres:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=llmwiki
    - POSTGRES_USER=llmwiki
    - POSTGRES_PASSWORD=your-secure-password
  volumes:
    - llmwiki_data:/var/lib/postgresql/data
```

Update DATABASE_URL in `.env`:
```env
DATABASE_URL=postgresql://llmwiki:password@postgres:5432/llmwiki
```

## Useful Docker Commands

### Container Management
```bash
# List running containers
docker ps

# List all containers
docker ps -a

# View container logs
docker logs llmwiki
docker logs llmwiki -f  # Follow logs
docker logs llmwiki -n 50  # Last 50 lines

# Execute command in running container
docker exec -it llmwiki bash
docker exec llmwiki python -c "import sys; print(sys.version)"

# Inspect container details
docker inspect llmwiki
```

### Image Management
```bash
# List images
docker images

# Remove image
docker rmi llmwiki:latest

# Tag image for registry
docker tag llmwiki:latest myregistry/llmwiki:v1.0

# Push to registry
docker push myregistry/llmwiki:v1.0
```

### Docker Compose Commands
```bash
# Start services
docker-compose up
docker-compose up -d  # Background mode

# Stop services
docker-compose stop

# Start stopped services
docker-compose start

# Restart services
docker-compose restart

# Remove stopped services
docker-compose rm

# View logs
docker-compose logs
docker-compose logs -f llmwiki

# Execute command in running service
docker-compose exec llmwiki bash

# Scale services (if needed)
docker-compose up -d --scale llmwiki=3
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs llmwiki

# Common issues:
# 1. Port 8000 already in use
#    - Change port: docker run -p 8001:8000
# 2. API key not set
#    - Add: -e GEMINI_API_KEY=your-key
# 3. Database permission issues
#    - Check volume permissions
```

### Database connection errors
```bash
# Verify database file exists
docker exec llmwiki ls -la /app/llmwiki.db

# Check database integrity
docker exec llmwiki sqlite3 /app/llmwiki.db ".tables"
```

### Permission denied errors
```bash
# Fix file permissions on host
chmod 777 llmwiki.db

# Rebuild image with correct user
docker-compose build --no-cache
```

### Memory/CPU issues
Modify resource limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

## Production Deployment

### 1. Use a Production Database
Switch from SQLite to PostgreSQL (see Database Options above)

### 2. Update Secrets
```env
SECRET_KEY=generate-a-strong-random-key-here
# Use: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Use Docker Secrets (Swarm) or Kubernetes Secrets
```bash
# Docker Swarm
echo "your-secret-key" | docker secret create jwt_secret -

# Then reference in docker-compose.yml
secrets:
  jwt_secret:
    external: true
```

### 4. Set up Reverse Proxy (nginx)
```nginx
upstream llmwiki {
    server llmwiki:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://llmwiki;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Enable HTTPS with Let's Encrypt
```bash
# Using Certbot in Docker
docker run --rm -it \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com
```

### 6. Docker Swarm Deployment
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml llmwiki

# Monitor stack
docker stack services llmwiki

# Remove stack
docker stack rm llmwiki
```

## Development with Docker

### Live Code Reload
Uncomment the volume mount in `docker-compose.yml`:
```yaml
volumes:
  - .:/app  # Live reload during development
```

### Run Tests
```bash
docker-compose exec llmwiki python -m pytest
```

### Debug Mode
```bash
docker run -it \
  -p 8000:8000 \
  -e DEBUG=True \
  -v $(pwd):/app \
  llmwiki:latest python -m pdb server.py
```

## Security Considerations

1. **Never commit secrets to version control**
   - Use `.env` file (add to `.gitignore`)
   - Use environment variables or secret management tools

2. **Use non-root user in container**
   - Dockerfile includes `useradd` for security

3. **Enable HTTPS in production**
   - Use reverse proxy with SSL termination
   - Let's Encrypt for free certificates

4. **Keep dependencies updated**
   ```bash
   pip install --upgrade pip
   pip-audit  # Check for vulnerabilities
   ```

5. **Scan images for vulnerabilities**
   ```bash
   docker scan llmwiki:latest
   trivy image llmwiki:latest
   ```

## Monitoring

### Docker Stats
```bash
# Monitor resource usage
docker stats llmwiki

# Monitor network
docker stats --no-stream
```

### Logging
```bash
# View all logs
docker-compose logs

# Filter by service
docker-compose logs llmwiki

# Last 100 lines
docker-compose logs --tail=100

# Follow in real-time
docker-compose logs -f

# Timestamp format
docker-compose logs --timestamps
```

## Backup and Recovery

### Backup Database
```bash
# Stop container (optional, DB is accessible while running)
docker-compose stop llmwiki

# Copy database
docker cp llmwiki:/app/llmwiki.db ./backup/llmwiki-$(date +%Y%m%d-%H%M%S).db

# Restart
docker-compose start llmwiki
```

### Restore Database
```bash
# Copy backup back
docker cp ./backup/llmwiki-backup.db llmwiki:/app/llmwiki.db

# Restart to apply
docker-compose restart llmwiki
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment Docs](https://fastapi.tiangolo.com/deployment/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
