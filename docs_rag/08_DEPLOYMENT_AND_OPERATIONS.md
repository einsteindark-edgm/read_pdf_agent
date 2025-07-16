# Deployment and Operations - Production Ready Guide

## Context for RAG
This document covers deployment, monitoring, and operational aspects of the Document Extraction Agent. It includes Docker setup, environment configurations, monitoring, scaling, and troubleshooting production issues.

## Docker Deployment

### Complete Dockerfile
```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 agent
USER agent

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=agent:agent . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/.well-known/agent.json')"

# Expose A2A port
EXPOSE 8080

# Run server
CMD ["python", "__main__.py"]
```

### Docker Compose Setup
```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - MCP_PDF_SERVER_DIR=/data/pdfs
      - MCP_PDF_SERVER_COMMAND=python
      - MCP_PDF_SERVER_ARGS=/app/mcp_server/server.py
      - LOG_LEVEL=INFO
    volumes:
      - ./data/pdfs:/data/pdfs:ro  # Read-only PDF mount
    restart: unless-stopped
    networks:
      - agent-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    networks:
      - agent-network
    volumes:
      - redis-data:/data

  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge

volumes:
  redis-data:
  prometheus-data:
```

### ERROR: Common Docker Issues

#### Issue: MCP server can't access PDFs
```bash
Failed to initialize MCP server: [Errno 2] No such file or directory
```

**Fix**: Ensure volume mount is correct
```yaml
volumes:
  - ${LOCAL_PDF_DIR}:/data/pdfs:ro  # Absolute path on host
```

#### Issue: Out of memory
```bash
Container killed due to OOM
```

**Fix**: Increase memory limits or optimize
```yaml
deploy:
  resources:
    limits:
      memory: 4G  # Increase for large PDFs
```

## Environment Configuration

### Production .env File
```bash
# API Keys (use secrets management in production)
GOOGLE_API_KEY=your-production-key

# MCP Configuration
MCP_PDF_SERVER_DIR=/data/pdfs
MCP_PDF_SERVER_COMMAND=python
MCP_PDF_SERVER_ARGS=/app/mcp_server/server.py
MCP_PDF_TRANSPORT=stdio

# Server Configuration
HOST=0.0.0.0
PORT=8080
WORKERS=4  # Number of worker processes

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # For structured logging

# Performance
MAX_PDF_SIZE_KB=1024  # 1MB limit
REQUEST_TIMEOUT=60  # seconds
LLM_TIMEOUT=30  # seconds

# Optional Features
ENABLE_METRICS=true
ENABLE_CACHE=true
CACHE_URL=redis://redis:6379
```

### Secrets Management
```python
# In /app/infrastructure/config/secrets.py
import os
from typing import Optional

class SecretsManager:
    """Manage secrets from various sources."""
    
    @staticmethod
    def get_api_key() -> str:
        """Get API key from environment or secrets manager."""
        # Option 1: Environment variable
        key = os.getenv("GOOGLE_API_KEY")
        
        # Option 2: AWS Secrets Manager
        if not key and os.getenv("USE_AWS_SECRETS"):
            import boto3
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId='google-api-key')
            key = response['SecretString']
        
        # Option 3: Kubernetes secrets
        if not key and os.path.exists("/var/run/secrets/api-key"):
            with open("/var/run/secrets/api-key", "r") as f:
                key = f.read().strip()
        
        if not key:
            raise ValueError("No API key found")
        
        return key
```

## Kubernetes Deployment

### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-extraction-agent
  labels:
    app: extraction-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: extraction-agent
  template:
    metadata:
      labels:
        app: extraction-agent
    spec:
      containers:
      - name: agent
        image: your-registry/extraction-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: google-api-key
        - name: MCP_PDF_SERVER_DIR
          value: "/data/pdfs"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /.well-known/agent.json
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /.well-known/agent.json
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: pdf-storage
          mountPath: /data/pdfs
          readOnly: true
      volumes:
      - name: pdf-storage
        persistentVolumeClaim:
          claimName: pdf-storage-pvc
```

### Service and Ingress
```yaml
apiVersion: v1
kind: Service
metadata:
  name: extraction-agent-service
spec:
  selector:
    app: extraction-agent
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: extraction-agent-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
spec:
  rules:
  - host: extraction-agent.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: extraction-agent-service
            port:
              number: 80
```

## Monitoring and Observability

### Structured Logging
```python
# In /app/infrastructure/logging/setup.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'exc_info', 'exc_text', 'stack_info',
                          'pathname', 'processName', 'relativeCreated']:
                log_data[key] = value
        
        return json.dumps(log_data)

# Configure logging
def setup_logging():
    """Setup structured logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        handlers=[handler]
    )
```

### Metrics Collection
```python
# In /app/infrastructure/metrics/prometheus.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'extraction_requests_total',
    'Total number of extraction requests',
    ['status', 'document_type']
)

request_duration = Histogram(
    'extraction_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

active_requests = Gauge(
    'extraction_active_requests',
    'Number of active requests'
)

mcp_tools_available = Gauge(
    'mcp_tools_available',
    'Number of available MCP tools'
)

# Use in code
class MetricsMiddleware:
    """Middleware to collect metrics."""
    
    async def __call__(self, request, call_next):
        active_requests.inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            request_count.labels(
                status='success',
                document_type='unknown'
            ).inc()
            return response
            
        except Exception as e:
            request_count.labels(
                status='error',
                document_type='unknown'
            ).inc()
            raise
            
        finally:
            duration = time.time() - start_time
            request_duration.labels(
                endpoint=request.url.path
            ).observe(duration)
            active_requests.dec()
```

### Health Checks
```python
# In /app/infrastructure/web/health.py
from fastapi import APIRouter
from typing import Dict, Any
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check - verify all components."""
    checks = {
        "mcp": await check_mcp(),
        "llm": await check_llm(),
        "memory": check_memory()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }

async def check_mcp() -> bool:
    """Check if MCP is responsive."""
    try:
        # Try to get tools
        from app.main.composition_root import get_composition_root
        root = get_composition_root()
        if hasattr(root._mcp_client, '_initialized'):
            return root._mcp_client._initialized
        return False
    except:
        return False

async def check_llm() -> bool:
    """Check if LLM is accessible."""
    try:
        # Quick test call
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-exp")
        await llm.ainvoke("test")
        return True
    except:
        return False

def check_memory() -> bool:
    """Check memory usage."""
    import psutil
    memory = psutil.virtual_memory()
    # Alert if > 80% memory used
    return memory.percent < 80
```

## Performance Optimization

### Caching Strategy
```python
# In /app/infrastructure/external_services/cache_decorator.py
from functools import wraps
import hashlib
import json

def cache_result(ttl: int = 300):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'cache') or not self.cache:
                return await func(self, *args, **kwargs)
            
            # Create cache key
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Check cache
            cached = await self.cache.get(cache_key)
            if cached:
                return cached
            
            # Execute and cache
            result = await func(self, *args, **kwargs)
            await self.cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Usage
class LangChainExtractionAgent:
    @cache_result(ttl=600)  # Cache for 10 minutes
    async def process_message(self, message: str) -> Dict[str, Any]:
        # Expensive operation cached
        ...
```

### Connection Pooling
```python
# In /app/infrastructure/config/connections.py
import httpx
from typing import Optional

class ConnectionManager:
    """Manage connection pools."""
    
    _http_client: Optional[httpx.AsyncClient] = None
    
    @classmethod
    async def get_http_client(cls) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if cls._http_client is None:
            cls._http_client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                ),
                timeout=httpx.Timeout(30.0)
            )
        return cls._http_client
    
    @classmethod
    async def close_all(cls):
        """Close all connections."""
        if cls._http_client:
            await cls._http_client.aclose()
            cls._http_client = None
```

## Scaling Strategies

### Horizontal Scaling
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: extraction-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: document-extraction-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Load Balancing
```nginx
# Nginx configuration for multiple instances
upstream extraction_agents {
    least_conn;  # Use least connections algorithm
    
    server agent1:8080 max_fails=3 fail_timeout=30s;
    server agent2:8080 max_fails=3 fail_timeout=30s;
    server agent3:8080 max_fails=3 fail_timeout=30s;
    
    keepalive 32;  # Keep connections alive
}

server {
    listen 80;
    server_name extraction-agent.example.com;
    
    location / {
        proxy_pass http://extraction_agents;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Backup and Recovery

### PDF Storage Backup
```bash
#!/bin/bash
# backup_pdfs.sh

BACKUP_DIR="/backups/pdfs"
PDF_DIR="/data/pdfs"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf "$BACKUP_DIR/pdfs_$DATE.tar.gz" -C "$PDF_DIR" .

# Keep only last 7 days
find "$BACKUP_DIR" -name "pdfs_*.tar.gz" -mtime +7 -delete

# Sync to S3 (optional)
aws s3 sync "$BACKUP_DIR" s3://your-bucket/pdf-backups/
```

### State Recovery
```python
# In /app/infrastructure/recovery/state.py
class StateRecovery:
    """Handle graceful recovery after crashes."""
    
    @staticmethod
    async def recover_mcp_connection():
        """Recover MCP connection after failure."""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                from app.main.composition_root import get_composition_root
                root = get_composition_root()
                
                # Force re-initialization
                root._mcp_client._initialized = False
                await root._mcp_client.initialize()
                
                logger.info("MCP connection recovered")
                return True
                
            except Exception as e:
                logger.error(f"Recovery attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay * (attempt + 1))
        
        return False
```

## Production Checklist

### Pre-Deployment
- [ ] All environment variables documented
- [ ] Secrets management configured
- [ ] Health checks implemented
- [ ] Metrics endpoints exposed
- [ ] Logging configured for production
- [ ] Resource limits set
- [ ] Backup strategy defined

### Deployment
- [ ] Blue-green deployment setup
- [ ] Rollback procedure documented
- [ ] Load balancer health checks
- [ ] SSL/TLS certificates
- [ ] Rate limiting configured
- [ ] DDoS protection enabled

### Post-Deployment
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Log aggregation working
- [ ] Performance baselines established
- [ ] Runbooks created
- [ ] On-call rotation setup

## Troubleshooting Production Issues

### High Memory Usage
```bash
# Check memory usage
docker stats

# Analyze memory dump
python -m py_spy dump --pid <PID>
```

**Common causes**:
1. Large PDFs not released
2. Memory leaks in MCP subprocess
3. Too many concurrent requests

### Slow Response Times
```python
# Add request timing
import time

async def timed_operation(name: str, operation):
    """Time an operation."""
    start = time.time()
    try:
        result = await operation()
        duration = time.time() - start
        logger.info(f"{name} took {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start
        logger.error(f"{name} failed after {duration:.2f}s: {e}")
        raise
```

### MCP Subprocess Issues
```bash
# Check if MCP processes are running
ps aux | grep mcp

# Kill zombie processes
pkill -f "mcp_documents_server"
```

## Summary

Production deployment requires:
1. **Containerization** - Docker with proper resource limits
2. **Orchestration** - Kubernetes or Docker Swarm
3. **Monitoring** - Metrics, logs, and traces
4. **Scaling** - Horizontal scaling with load balancing
5. **Recovery** - Graceful handling of failures
6. **Security** - Secrets management and network policies

The system is designed to be cloud-native and scalable.

## Next: Read 09_API_REFERENCE.md
For complete API documentation and examples.