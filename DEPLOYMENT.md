# GreenMind Deployment Guide

## Production Deployment

### Prerequisites
- Python 3.8+
- Linux/Windows/macOS
- 4GB+ RAM
- 2GB+ disk space
- Stable internet connection

## Deployment Steps

### 1. Server Setup

#### Option 1: Linux Server (Ubuntu/Debian)
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python
sudo apt-get install python3 python3-pip python3-venv

# Clone project
git clone <repository_url>
cd CapstoneProject

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

#### Option 2: Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose port for Streamlit
EXPOSE 8501

CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Environment Setup
```bash
# Create .env file
cp .env.example .env

# Edit .env with production values
nano .env
```

### 3. Initialize Application
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize sample data (optional)
python initialize_sample_data.py

# Setup project
python setup.py

# Run tests
python test_setup.py
```

### 4. Run Application

#### Local Development
```bash
streamlit run src/ui/streamlit_app.py
```

#### Production with Gunicorn
```bash
pip install gunicorn

# Configure as a service (Linux)
sudo tee /etc/systemd/system/greenmind.service > /dev/null <<EOF
[Unit]
Description=GreenMind Sustainability Advisor
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/CapstoneProject
ExecStart=/path/to/venv/bin/streamlit run src/ui/streamlit_app.py

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable greenmind
sudo systemctl start greenmind
```

### 5. Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Production Optimization

### 1. Performance Tuning
```bash
# Increase file descriptors
ulimit -n 65536

# Enable swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 2. Load Balancing
- Use multiple instances behind a load balancer
- Implement session management
- Cache frequently accessed data

### 3. Security Measures
```bash
# UFW Firewall (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. SSL/TLS Certificate
```bash
# Using Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx

sudo certbot certonly --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring and Maintenance

### 1. Log Monitoring
```bash
# View logs
tail -f logs/greenmind_*.log

# Log rotation
sudo apt-get install logrotate

# Configure log rotation
sudo tee /etc/logrotate.d/greenmind > /dev/null <<EOF
/path/to/CapstoneProject/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
EOF
```

### 2. System Monitoring
```bash
# Monitor resource usage
watch -n 1 free -h
watch -n 1 top -p <PID>

# Check disk usage
df -h
du -sh /path/to/CapstoneProject
```

### 3. Database Maintenance
```bash
# Rebuild vector database
python -c "from src.rag.vector_db import VectorDatabase; v = VectorDatabase(); v.clear()"
python setup.py
```

## Backup Strategy

### 1. Regular Backups
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/greenmind"
SOURCE_DIR="/path/to/CapstoneProject"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz $SOURCE_DIR/logs/

# Backup vector database
tar -czf $BACKUP_DIR/vector_db_$DATE.tar.gz $SOURCE_DIR/vector_db/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz $SOURCE_DIR/.env $SOURCE_DIR/config/

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 2. Automated Backup with Cron
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

## Scaling Strategies

### 1. Horizontal Scaling
- Deploy multiple instances
- Use load balancer (Nginx, HAProxy)
- Shared vector database
- Common logs storage

### 2. Caching Layer
- Implement Redis for response caching
- Cache frequently asked questions
- Reduce API calls

### 3. Database Optimization
- Partition vector database
- Use approximate nearest neighbors (ANN)
- Implement search result caching

## Troubleshooting

### Memory Issues
```bash
# Increase available memory
free -h
vmstat
ps aux --sort=-%mem | head
```

### API Rate Limiting
- Implement request queuing
- Use API batching
- Cache responses appropriately

### PDF Loading Issues
```bash
# Verify PDF integrity
pdfinfo <filename>.pdf
pdfseparate <filename>.pdf page-%d.txt
```

## Rollback Procedures

### Rollback to Previous Version
```bash
# Stop service
sudo systemctl stop greenmind

# Restore from backup
tar -xzf /backups/greenmind/backup_<date>.tar.gz

# Restart service
sudo systemctl start greenmind

# Verify operation
curl http://localhost:8501
```

## Performance Benchmarks

Expected Performance Metrics:
- Query Response Time: < 5 seconds
- Vector Search: < 500ms
- API Throughput: 100+ requests/minute
- Uptime: 99.9%

## Support and Maintenance

- Monitor logs daily
- Update dependencies monthly
- Test disaster recovery quarterly
- Review security monthly

---

**Last Updated**: April 2026
**Version**: 1.0.0
