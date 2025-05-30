#!/bin/bash

# SSL Deployment Script for PDF2Markdown
# This script sets up SSL certificates and configures Nginx

set -e  # Exit on any error

echo "🚀 Starting SSL deployment for PDF2Markdown..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root. Please run as a regular user.${NC}"
   exit 1
fi

# Set proper permissions for SSL files
echo "🔒 Setting SSL file permissions..."
sudo chmod 644 /etc/ssl/certs/pdf2markdown.tech.pem
sudo chmod 600 /etc/ssl/private/pdf2markdown.tech.key
sudo chown root:root /etc/ssl/certs/pdf2markdown.tech.pem
sudo chown root:root /etc/ssl/private/pdf2markdown.tech.key

echo -e "${GREEN}✓ SSL permissions set${NC}"

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y nginx
    echo -e "${GREEN}✓ Nginx installed${NC}"
else
    echo -e "${GREEN}✓ Nginx already installed${NC}"
fi

# Backup existing Nginx configuration
if [[ -f "/etc/nginx/sites-enabled/default" ]]; then
    echo "📦 Backing up default Nginx configuration..."
    sudo cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup
fi

# Copy Nginx configuration
echo "⚙️  Configuring Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/pdf2markdown.tech

# Enable the site
sudo ln -sf /etc/nginx/sites-available/pdf2markdown.tech /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration test failed!${NC}"
    exit 1
fi

# Reload Nginx
echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx reloaded successfully${NC}"

# Check if services are running
echo "🔍 Checking service status..."

# Check if ports are available
if netstat -tlnp 2>/dev/null | grep -q ":8001 "; then
    echo -e "${GREEN}✓ Backend service running on port 8001${NC}"
else
    echo -e "${YELLOW}⚠️  Backend service not detected on port 8001${NC}"
    echo "   Start with: cd backend && uvicorn main:app --host 0.0.0.0 --port 8001"
fi

if netstat -tlnp 2>/dev/null | grep -q ":8002 "; then
    echo -e "${GREEN}✓ Frontend service running on port 8002${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend service not detected on port 8002${NC}"
    echo "   Start with: cd frontend && npm start -- -p 8002"
fi

# Test SSL certificate
echo "🔐 Testing SSL certificate..."
if openssl x509 -in /etc/ssl/certs/pdf2markdown.tech.pem -text -noout > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SSL certificate is valid${NC}"
    
    # Show certificate expiration
    EXPIRY=$(openssl x509 -in /etc/ssl/certs/pdf2markdown.tech.pem -text -noout | grep "Not After" | cut -d: -f2-)
    echo "   Certificate expires:$EXPIRY"
else
    echo -e "${RED}❌ SSL certificate validation failed!${NC}"
    exit 1
fi

# Final status
echo ""
echo -e "${GREEN}🎉 SSL deployment completed successfully!${NC}"
echo ""
echo "Your site is now available at:"
echo -e "  ${GREEN}https://pdf2markdown.tech${NC}"
echo ""
echo "Next steps:"
echo "1. Start your backend service (port 8001)"
echo "2. Start your frontend service (port 8002)"
echo "3. Test the deployment with: curl https://pdf2markdown.tech/api/health"
echo ""
echo "Logs:"
echo "  Nginx access: sudo tail -f /var/log/nginx/access.log"
echo "  Nginx error:  sudo tail -f /var/log/nginx/error.log" 