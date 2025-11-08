# 🚀 AutoCodit Agent - Deployment Guide

## Prerequisites

### Required Software
- Docker 24.0+ and Docker Compose 2.20+
- Node.js 18+ (for local development)
- Git 2.30+
- Python 3.11+ (for backend development)

### Required Accounts & Credentials
- GitHub App (for bot integration)
- OpenAI API key (or Anthropic/local LLM)
- Domain with SSL certificate (for production)

---

## 🔧 Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/arturwyroslak/autocodit-agent.git
cd autocodit-agent
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Minimum required variables:
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nYour key\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret
OPENAI_API_KEY=sk-your-openai-key
JWT_SECRET=$(openssl rand -hex 32)
```

### 3. GitHub App Setup

#### Create GitHub App:

1. Go to: `https://github.com/settings/apps/new`
2. Fill in:
   - **GitHub App name:** `AutoCodit Agent [Your Org]`
   - **Homepage URL:** `https://your-domain.com`
   - **Webhook URL:** `https://your-domain.com/api/v1/github/webhook`
   - **Webhook secret:** Generate random string (save to `.env`)

3. Permissions:
   ```
   Repository permissions:
   - Contents: Read & Write
   - Issues: Read & Write
   - Pull requests: Read & Write
   - Metadata: Read-only
   - Workflows: Read & Write (optional)
   ```

4. Subscribe to events:
   - Issues
   - Issue comments
   - Pull requests
   - Pull request reviews
   - Push

5. Save and generate private key (download `.pem` file)

6. Convert key to single-line for `.env`:
   ```bash
   cat your-app.pem | awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}'
   ```

7. Install app to your organization/repositories

---

## 🐳 Docker Deployment

### Development Mode

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api frontend

# Stop services
docker-compose down
```

#### Service Ports (Development):
- **Frontend:** http://localhost:3001
- **Backend API:** http://localhost:8001
- **Database:** localhost:5433
- **Redis:** localhost:6378
- **MinIO Console:** http://localhost:9003
- **Prometheus:** http://localhost:9091
- **Grafana:** http://localhost:3002

### Production Mode

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Or build with specific version
docker-compose -f docker-compose.prod.yml build --build-arg VERSION=1.0.0
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔄 Database Setup

### Initial Migration

```bash
# Run migrations (automatic on first start)
docker-compose exec api alembic upgrade head

# Create initial admin user
docker-compose exec api python -m app.cli create-admin \
  --email admin@example.com \
  --password your-secure-password
```

### Manual Schema Creation

If auto-migration fails:

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U autocodit -d autocodit_agent

# Run schema manually
\i /docker-entrypoint-initdb.d/02-schema.sql
```

---

## 🌐 Frontend Configuration

### Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
NEXT_PUBLIC_APP_NAME=AutoCodit Agent
```

### Build & Deploy

```bash
cd frontend
npm install
npm run build
npm start
```

Or with Docker (automatically handled by docker-compose):

```bash
docker-compose up --build frontend
```

---

## 🚨 Troubleshooting

### Frontend: Module not found errors

**Problem:** `Can't resolve '@radix-ui/react-select'`

**Solution:**
```bash
# Rebuild frontend container with fresh dependencies
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Backend: Database connection failed

**Problem:** `Could not connect to PostgreSQL`

**Solution:**
```bash
# Check database is healthy
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db

# Wait for healthy status
docker-compose exec db pg_isready -U autocodit
```

### API: GitHub webhook not working

**Problem:** Webhooks return 401/403

**Solution:**
1. Check webhook secret matches `.env`
2. Verify GitHub App is installed
3. Check API logs: `docker-compose logs api | grep webhook`
4. Test webhook manually:
   ```bash
   curl -X POST http://localhost:8001/api/v1/github/webhook \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: ping" \
     -d '{"zen": "test"}'
   ```

### Worker: Tasks not processing

**Problem:** Tasks stuck in "queued" status

**Solution:**
```bash
# Check worker status
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# Monitor queue
docker-compose exec redis redis-cli -n 1 LLEN celery
```

---

## 🔐 Security Hardening

### Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong JWT_SECRET (32+ chars)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set `DEBUG=false` in production
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up backup strategy
- [ ] Configure monitoring alerts
- [ ] Review GitHub App permissions
- [ ] Enable audit logging

### SSL/TLS Setup

For production with nginx reverse proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📊 Monitoring Setup

### Prometheus

Metrics available at: `http://localhost:9091`

### Grafana

1. Access: `http://localhost:3002`
2. Login: `admin` / `admin123`
3. Add datasource: Prometheus at `http://prometheus:9090`
4. Import dashboard: `./monitoring/grafana/dashboards/autocodit.json`

### Health Checks

```bash
# API health
curl http://localhost:8001/health

# Detailed status
curl http://localhost:8001/api/v1/endpoints/health

# Service info
curl http://localhost:8001/api/v1/endpoints/health/info
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### Backup Database

```bash
# Backup
docker-compose exec db pg_dump -U autocodit autocodit_agent > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20240101.sql | docker-compose exec -T db psql -U autocodit autocodit_agent
```

### Clean Up Resources

```bash
# Remove stopped containers
docker-compose down --volumes

# Prune unused images
docker system prune -af

# Clean build cache
docker builder prune -af
```

---

## ☸️ Kubernetes Deployment

### Using Helm Chart

```bash
# Add Helm repository
helm repo add autocodit https://charts.autocodit.dev
helm repo update

# Install
helm install autocodit-agent autocodit/autocodit-agent \
  --namespace autocodit-agent \
  --create-namespace \
  --set github.appId=YOUR_APP_ID \
  --set github.privateKey="YOUR_PRIVATE_KEY" \
  --set github.webhookSecret=YOUR_WEBHOOK_SECRET \
  --set openai.apiKey=YOUR_OPENAI_KEY \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=autocodit.yourdomain.com
```

### Custom Values

Create `values.yaml`:

```yaml
replicaCount:
  api: 3
  worker: 5
  frontend: 2

resources:
  api:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: autocodit.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: autocodit-tls
      hosts:
        - autocodit.yourdomain.com
```

Deploy with custom values:

```bash
helm install autocodit-agent autocodit/autocodit-agent \
  -f values.yaml \
  --namespace autocodit-agent
```

---

## 🧪 Testing Deployment

### 1. Verify Services

```bash
# Check all containers running
docker-compose ps

# Should show:
# - api (healthy)
# - frontend (running)
# - worker (running)
# - db (healthy)
# - redis (healthy)
```

### 2. Test Frontend

```bash
curl http://localhost:3001
# Should return HTML
```

### 3. Test API

```bash
# Health check
curl http://localhost:8001/health

# API root
curl http://localhost:8001/api/v1/

# List tasks (should return empty array initially)
curl http://localhost:8001/api/v1/tasks
```

### 4. Test GitHub Webhook

1. Go to your GitHub App settings
2. Click "Recent Deliveries"
3. Find the "ping" event
4. Click "Redeliver"
5. Check response is 200 OK

### 5. Create Test Task

```bash
curl -X POST http://localhost:8001/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Add a README to the repository",
    "repository": "yourorg/yourrepo",
    "branch": "main",
    "action_type": "plan",
    "priority": "normal"
  }'
```

---

## 🌍 Production Deployment

### Option 1: VPS/Cloud Server (Digital Ocean, AWS EC2, etc.)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Clone repository
git clone https://github.com/arturwyroslak/autocodit-agent.git
cd autocodit-agent

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Setup SSL with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d autocodit.yourdomain.com
```

### Option 2: Kubernetes (GKE, EKS, AKS)

```bash
# Create namespace
kubectl create namespace autocodit-agent

# Create secrets
kubectl create secret generic github-app-secret \
  --from-literal=app-id=YOUR_APP_ID \
  --from-file=private-key=./github-app.pem \
  --from-literal=webhook-secret=YOUR_WEBHOOK_SECRET \
  -n autocodit-agent

kubectl create secret generic openai-secret \
  --from-literal=api-key=YOUR_OPENAI_KEY \
  -n autocodit-agent

# Install with Helm
helm install autocodit-agent ./charts/autocodit-agent \
  -f production-values.yaml \
  -n autocodit-agent

# Check deployment
kubectl get pods -n autocodit-agent
kubectl get svc -n autocodit-agent
```

### Option 3: Vercel (Frontend Only)

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## 🔍 Verification

### Post-Deployment Checks

```bash
#!/bin/bash
# save as verify.sh and run: bash verify.sh

echo "🔍 Verifying AutoCodit Agent deployment..."

# Check API health
echo "\n✅ API Health:"
curl -s http://localhost:8001/health | jq .

# Check database
echo "\n✅ Database:"
docker-compose exec -T db pg_isready -U autocodit

# Check Redis
echo "\n✅ Redis:"
docker-compose exec -T redis redis-cli ping

# Check frontend
echo "\n✅ Frontend:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001

# Check worker
echo "\n✅ Worker:"
docker-compose exec worker celery -A workers.celery_app inspect active

echo "\n✅ All checks completed!"
```

---

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  api:
    deploy:
      replicas: 3
  
  worker:
    deploy:
      replicas: 5
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy AutoCodit Agent

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push Docker images
        run: |
          docker build -t autocodit/api:${{ github.sha }} ./backend
          docker build -t autocodit/frontend:${{ github.sha }} ./frontend
          docker push autocodit/api:${{ github.sha }}
          docker push autocodit/frontend:${{ github.sha }}
      
      - name: Deploy to production
        run: |
          ssh deploy@your-server.com "cd /opt/autocodit-agent && \
            docker-compose pull && \
            docker-compose up -d && \
            docker-compose exec api alembic upgrade head"
```

---

## 📞 Support

### Common Issues

1. **Port conflicts:** Change ports in `docker-compose.yml`
2. **Memory issues:** Increase Docker memory limit
3. **Network issues:** Check firewall rules
4. **Permission issues:** Ensure user in docker group

### Getting Help

- 📖 [Documentation](./docs/README.md)
- 💬 [Discord Community](https://discord.gg/autocodit)
- 🐛 [GitHub Issues](https://github.com/arturwyroslak/autocodit-agent/issues)
- 📧 Email: support@autocodit.dev

---

## 🎯 Next Steps

After successful deployment:

1. ✅ Access dashboard at `http://localhost:3001`
2. ✅ Create your first task
3. ✅ Install GitHub App to repositories
4. ✅ Test bot with `@autocodit-bot plan: Add tests`
5. ✅ Configure monitoring and alerts
6. ✅ Set up backup strategy
7. ✅ Review security settings

---

**🎉 Congratulations! Your AutoCodit Agent is now running!**
