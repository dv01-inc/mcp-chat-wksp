# 🐳 Container Guide for AI Service

Complete guide for containerizing and deploying the AI Service with PostgreSQL using Podman or Docker.

## 📋 Overview

The AI Service is fully containerized using Podman Compose (or Docker Compose) with:
- **Gateway Service**: FastAPI application with intelligent MCP routing
- **PostgreSQL Database**: Persistent chat history and user data
- **Health Checks**: Built-in monitoring and retry logic
- **Development Mode**: Mock authentication and automatic setup

## 🏗️ Container Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Docker Network                           │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │   PostgreSQL    │    │        Gateway              │ │
│  │  postgres:15    │    │    mcp-gateway:latest       │ │
│  │  Port: 5432     │────│    Port: 8000               │ │
│  │  Volume: data   │    │    Depends: postgres        │ │
│  │  Health: ready  │    │    Health: /health          │ │
│  └─────────────────┘    └─────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            │
                   ┌─────────────────┐
                   │   Host Network   │
                   │  localhost:8000 │
                   │  localhost:5433 │
                   └─────────────────┘
```

## 🚀 Quick Start

### Using Nx (Recommended)

```bash
# Start everything
pnpm containers:up

# Check status
pnpm containers:status

# View logs
pnpm containers:logs

# Stop everything
pnpm containers:down
```

### Using Docker Compose

```bash
cd apps/mcp-gateway

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📁 File Structure

```
apps/mcp-gateway/
├── Dockerfile                 # Gateway container definition
├── docker-compose.yml         # Multi-service orchestration
├── .dockerignore              # Files to exclude from build
├── requirements-docker.txt    # Python dependencies for container
├── mcp_gateway/              # Application source code
│   ├── main.py               # FastAPI application
│   ├── database.py           # SQLAlchemy models and repos
│   ├── auth.py               # JWT and mock authentication
│   └── mcp_client.py         # MCP server communication
└── README.md                 # Complete documentation
```

## 🐳 Dockerfile Breakdown

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy the application code
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "mcp_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key Features:
- **Multi-stage optimization**: Minimal production image
- **Security**: Non-root user execution
- **Health monitoring**: Built-in health checks
- **Dependencies**: Only required packages included

## 🐘 PostgreSQL Configuration

### Environment Variables
```yaml
environment:
  POSTGRES_DB: mcp_gateway
  POSTGRES_USER: mcp_user
  POSTGRES_PASSWORD: mcp_password
```

### Volume Persistence
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

### Health Check
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U mcp_user -d mcp_gateway"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## ⚙️ Environment Configuration

### Gateway Environment Variables

| Variable | Container Value | Description |
|----------|----------------|-------------|
| `DATABASE_URL` | `postgresql://mcp_user:mcp_password@postgres:5432/mcp_gateway` | Internal database connection |
| `ENVIRONMENT` | `development` | Enables mock authentication |
| `ANTHROPIC_API_KEY` | `${ANTHROPIC_API_KEY}` | From host environment |
| `OPENAI_API_KEY` | `${OPENAI_API_KEY}` | From host environment |

### Host Environment Setup
```bash
# Create .env file in apps/mcp-gateway/
echo "ANTHROPIC_API_KEY=your_anthropic_key" >> .env
echo "OPENAI_API_KEY=your_openai_key" >> .env
```

## 🔗 Networking

### Internal Communication
- Gateway → PostgreSQL: `postgres:5432` (internal Docker network)
- Services communicate via Docker Compose network

### External Access
- Gateway API: `localhost:8000`
- PostgreSQL: `localhost:5433` (mapped from internal 5432)

### Port Configuration
```yaml
gateway:
  ports:
    - "8000:8000"
    
postgres:
  ports:
    - "5433:5432"  # Avoids conflict with host PostgreSQL
```

## 📊 Health Monitoring

### Gateway Health Check
```bash
# Container health
docker-compose ps

# Manual health check
curl http://localhost:8000/health
```

### PostgreSQL Health Check
```bash
# Database connectivity
docker exec -it mcp-gateway-postgres-1 pg_isready -U mcp_user

# Connect to database
docker exec -it mcp-gateway-postgres-1 psql -U mcp_user -d mcp_gateway
```

### Startup Sequence
1. **PostgreSQL starts** and becomes healthy
2. **Gateway waits** for database health check
3. **Gateway starts** and attempts database connection
4. **Retry logic** handles temporary connection failures
5. **Tables created** automatically on first startup
6. **Mock user created** in development mode

## 🔄 Container Lifecycle

### Development Workflow

```bash
# Start development environment
pnpm containers:up

# Make code changes
# (files are copied into container, so restart needed)

# Restart with new code
pnpm containers:restart

# View logs to debug
pnpm containers:logs

# Stop when done
pnpm containers:down
```

### Production Deployment

```bash
# Build optimized images
docker-compose build --no-cache

# Start in production mode
ENVIRONMENT=production docker-compose up -d

# Monitor logs
docker-compose logs -f gateway

# Scale gateway (multiple instances)
docker-compose up -d --scale gateway=3
```

## 📝 Logs and Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Gateway only
docker-compose logs -f gateway

# PostgreSQL only
docker-compose logs -f postgres

# Using Nx
npx nx container-logs mcp-gateway
```

### Log Levels
- **INFO**: Normal operations, health checks
- **ERROR**: Database connection failures, MCP errors
- **DEBUG**: Request/response details (if enabled)

### Key Log Messages
```
✅ Database tables created successfully
✅ Mock user created for development
🧠 Intelligent routing: 'prompt' → server
INFO: Uvicorn running on http://0.0.0.0:8000
```

## 🛠️ Customization

### Adding Environment Variables

1. **Update docker-compose.yml**:
   ```yaml
   gateway:
     environment:
       NEW_VARIABLE: ${NEW_VARIABLE}
   ```

2. **Update Dockerfile** (if needed):
   ```dockerfile
   ENV NEW_VARIABLE=${NEW_VARIABLE}
   ```

3. **Use in application**:
   ```python
   import os
   new_var = os.getenv("NEW_VARIABLE")
   ```

### Volume Mounts for Development

```yaml
gateway:
  volumes:
    - ./mcp_gateway:/app/mcp_gateway  # Live code reload
    - ./logs:/app/logs               # Log persistence
```

### Custom PostgreSQL Configuration

```yaml
postgres:
  environment:
    POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
  command: >
    postgres 
    -c shared_preload_libraries=pg_stat_statements
    -c pg_stat_statements.track=all
    -c max_connections=200
```

## 🔧 Troubleshooting

### Build Issues

**Python Dependencies Fail**:
```bash
# Clear build cache
docker system prune -a

# Rebuild with verbose output
docker-compose build --no-cache --progress=plain gateway
```

**Image Size Too Large**:
```bash
# Check image size
docker images mcp-gateway

# Optimize Dockerfile (use multi-stage builds)
# Remove unnecessary packages after installation
```

### Runtime Issues

**Container Exits Immediately**:
```bash
# Check exit code and logs
docker-compose ps
docker-compose logs gateway

# Common issues:
# - Missing environment variables
# - Port conflicts
# - Database connection failures
```

**Database Connection Refused**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check network connectivity
docker exec mcp-gateway-gateway-1 ping postgres

# Check environment variables
docker exec mcp-gateway-gateway-1 env | grep DATABASE_URL
```

**Port Already in Use**:
```bash
# Find process using port
lsof -i :8000
lsof -i :5433

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Different host port
```

### Performance Issues

**High Memory Usage**:
```bash
# Monitor container resources
docker stats

# Limit container memory
gateway:
  mem_limit: 512m
  mem_reservation: 256m
```

**Slow Database Queries**:
```bash
# Enable PostgreSQL query logging
postgres:
  command: postgres -c log_statement=all
```

## 🔐 Security Considerations

### Production Security

1. **Use Secrets Management**:
   ```yaml
   gateway:
     secrets:
       - db_password
       - jwt_secret
   ```

2. **Non-Root User**: Already implemented in Dockerfile

3. **Network Isolation**:
   ```yaml
   networks:
     backend:
       internal: true  # No external access
   ```

4. **Environment Variables**:
   - Never commit API keys to version control
   - Use Docker secrets or external secret managers
   - Rotate secrets regularly

### Container Security Scanning

```bash
# Scan for vulnerabilities
docker scout cves mcp-gateway

# Check for best practices
docker scout recommendations mcp-gateway
```

## 📈 Scaling and Load Balancing

### Horizontal Scaling

```bash
# Scale gateway instances
docker-compose up -d --scale gateway=3

# Use nginx for load balancing
# See nginx.conf example in docs/
```

### Database Scaling

```bash
# PostgreSQL read replicas
# See postgresql-replication.yml example

# Connection pooling
# Configure PgBouncer container
```

## 🚀 Deployment Options

### Local Development
```bash
# Quick start
pnpm containers:up
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
- name: Build and Deploy
  run: |
    docker-compose build
    docker-compose push
    docker-compose up -d
```

### Cloud Deployment
- **AWS ECS**: Use task definitions
- **Google Cloud Run**: Serverless container deployment
- **Kubernetes**: Use provided k8s manifests
- **DigitalOcean**: App Platform deployment

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Health Check Best Practices](https://docs.docker.com/engine/reference/builder/#healthcheck)