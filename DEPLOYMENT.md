# Production Deployment Guide

This guide explains how to deploy the PDF to Markdown Converter to production using Nginx as a reverse proxy.

## 🏗️ Architecture

```
Internet → pdf2markdown.tech:443 (HTTPS) → Nginx Reverse Proxy
                                              ├── / → Frontend (server:8002)
                                              └── /api → Backend (server:8001)
```

## 🚀 Deployment Steps

### 1. Server Setup

Ensure your server has the following services running:
- **Frontend**: Next.js app on port 8002
- **Backend**: FastAPI app on port 8001
- **vLLM**: Model server on port 8000 (internal)
- **SSL Certificates**: Located in `ssl/` directory

### 2. Install Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 3. SSL Certificate Setup

Your SSL certificates should be in the standard system SSL directories:
- **Certificate**: `/etc/ssl/certs/pdf2markdown.tech.pem`
- **Private Key**: `/etc/ssl/private/pdf2markdown.tech.key`

If you have certificates in your project's `ssl/` directory, move them to the system locations:
```bash
# Move certificates to system directories
sudo cp ssl/pdf2markdown.tech.pem /etc/ssl/certs/
sudo cp ssl/pdf2markdown.tech.key /etc/ssl/private/

# Set proper permissions
sudo chmod 644 /etc/ssl/certs/pdf2markdown.tech.pem
sudo chmod 600 /etc/ssl/private/pdf2markdown.tech.key
sudo chown root:root /etc/ssl/certs/pdf2markdown.tech.pem
sudo chown root:root /etc/ssl/private/pdf2markdown.tech.key
```

### 4. Configure Nginx

Copy the provided `nginx.conf` to your Nginx sites configuration:

```bash
# Copy the configuration
sudo cp nginx.conf /etc/nginx/sites-available/pdf2markdown.tech

# Enable the site
sudo ln -s /etc/nginx/sites-available/pdf2markdown.tech /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 5. Start Services

#### Backend (Port 8001)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### Frontend (Port 8002)
```bash
cd frontend
npm install
npm run build
npm start -- -p 8002
```

#### vLLM (Port 8000)
```bash
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --host 127.0.0.1 \
  --port 8000
```

### 6. Environment Variables

#### Frontend (.env.production)
```env
NEXT_PUBLIC_API_URL=/api
NODE_ENV=production
```

#### Backend
```env
VLLM_BASE_URL=http://127.0.0.1:8000
VLLM_AUTO_START=false
MAX_FILE_SIZE_MB=50
```

## 🔧 Nginx Configuration Explained

### API Routing (`/api/*`)
- **URL**: `pdf2markdown.tech/api/upload` 
- **Proxies to**: `127.0.0.1:8001/upload`
- **Features**: 
  - Removes `/api` prefix
  - Handles large file uploads (50MB)
  - Supports streaming responses
  - Disabled buffering for real-time streaming

### Frontend Routing (`/*`)
- **URL**: `pdf2markdown.tech/`
- **Proxies to**: `127.0.0.1:8002/`
- **Features**:
  - Static asset caching
  - Next.js specific optimizations
  - WebSocket support for hot reload

### Key Features
- **Security Headers**: XSS protection, frame options, etc.
- **Gzip Compression**: Reduces bandwidth usage
- **Caching**: Static assets cached for 1 year
- **Large Uploads**: Supports 50MB PDF files
- **Streaming**: Real-time response streaming

## 🔍 Testing the Setup

### 1. SSL Certificate Verification
```bash
# Test SSL certificate
openssl s_client -connect pdf2markdown.tech:443 -servername pdf2markdown.tech

# Check certificate expiration
openssl x509 -in /etc/ssl/certs/pdf2markdown.tech.pem -text -noout | grep "Not After"

# Verify certificate and key match
openssl x509 -noout -modulus -in /etc/ssl/certs/pdf2markdown.tech.pem | openssl md5
openssl rsa -noout -modulus -in /etc/ssl/private/pdf2markdown.tech.key | openssl md5
```

### 2. Health Check
```bash
# HTTPS (recommended)
curl https://pdf2markdown.tech/api/health

# HTTP (will redirect to HTTPS)
curl http://pdf2markdown.tech/api/health
```

### 3. Frontend Access
```bash
# HTTPS
curl https://pdf2markdown.tech/

# HTTP (will redirect)
curl -I http://pdf2markdown.tech/
```

### 4. File Upload Test
```bash
curl -X POST "https://pdf2markdown.tech/api/upload" \
  -F "file=@test.pdf"
```

## 🚨 Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check if backend/frontend services are running
- Verify port numbers (8001, 8002)
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

**Large File Upload Fails**
- Ensure `client_max_body_size 50M;` in Nginx config
- Check backend file size limits

**Streaming Not Working**
- Verify `proxy_buffering off;` in Nginx config
- Check WebSocket headers are properly set

**CORS Issues**
- Ensure proper proxy headers are set
- Check `X-Forwarded-*` headers

### Log Files
```bash
# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
# Backend: Check your FastAPI logs
# Frontend: Check Next.js logs
```

## 🔒 Security Considerations

### SSL/HTTPS (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d pdf2markdown.tech

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall
```bash
# Allow only necessary ports
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 📊 Monitoring

### Service Status
```bash
# Check Nginx
sudo systemctl status nginx

# Check if ports are listening
sudo netstat -tlnp | grep -E ':(80|8001|8002|8000)'
```

### Performance
- Monitor CPU/Memory usage
- Check response times
- Monitor disk space for uploads

## 🚀 Production Optimizations

### PM2 for Process Management
```bash
# Install PM2
npm install -g pm2

# Start frontend with PM2
pm2 start npm --name "pdf2md-frontend" -- start

# Start backend with PM2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8001" --name "pdf2md-backend"

# Save PM2 configuration
pm2 save
pm2 startup
```

### Docker Alternative
If you prefer Docker, update the docker-compose.yml ports:
```yaml
services:
  frontend:
    ports:
      - "8002:3000"
  backend:
    ports:
      - "8001:8001"
```

This deployment setup provides a robust, scalable solution for your PDF to Markdown converter with proper separation of concerns and production-ready configuration. 