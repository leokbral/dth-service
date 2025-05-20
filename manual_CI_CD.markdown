# Manual Deployment Process

0. Connect to VM via Hungria
```bash
ssh -p 4422 leonardocabral@177.20.147.141
ssh -p 4422 sciledger@10.7.40.192
```

1. Deployment Script Location
# The script should be in your home directory
cd ~
./sciledger_deploy.sh

2. Script Content (/home/sciledger/sciledger_deploy.sh)
```bash
#!/bin/bash

# Navigate to project directory
cd /var/www/sciledger

# Stash any local changes
git stash

# Pull latest changes
git pull origin main

# Install dependencies and build
npm ci
npm run build

# Stop all existing instances
pm2 delete sciledger

# Start new instance with correct host and port
pm2 start npm --name "sciledger" -- run preview -- --host --port 3000

# Save PM2 process list
pm2 save
```

2.5. Git Authentication Setup
```bash
# Set up Git credentials
cd /var/www/sciledger
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/leokbral/sciledger-online.git

# Verify remote URL is set correctly
git remote -v
```

3. Verify Deployment
```bash
# Check PM2 status
pm2 status

# Verify application is running
curl http://localhost:3000

# Test external access
curl http://10.7.40.192:3000

# View active ports
netstat -tulpn | grep LISTEN
```

4. Success Indicators
- HTML response from curl command
- MongoDB items visible in response
- No connection refused errors
- PM2 status shows "online"

5. Troubleshooting
- If port 3000 fails, check PM2 logs for actual port
- Ensure --host flag is set for network access
- Verify firewall allows port 3000
- Check MongoDB connection in application logs

6. External Access Testing
```bash
# From Hungria Server
curl http://10.7.40.192:3000

# From Windows Local Machine
curl http://177.20.147.141:3000

# From Web Browser
http://177.20.147.141:3000
```

7. Port Forwarding Requirements
- Port 3000 must be open on VM (already done)
- Port 3000 must be forwarded on Hungria server
- Check Hungria's port forwarding:
  ```bash
  # On Hungria
  sudo iptables -t nat -L
  ```

8. Troubleshooting External Access
- Verify VM firewall: `sudo ufw status`
- Check Hungria's forwarding: `sudo sysctl net.ipv4.ip_forward`
- Test network path: `tracert 177.20.147.141` (from Windows)
- Monitor access logs: `tail -f /var/log/nginx/access.log`

### Verify Application Access

```bash
# Check if application is running (it should be on port 3000)
curl http://localhost:3000

# Check actual port being used (if 3000 fails)
curl http://localhost:4173
curl http://localhost:4174

# Check process and port
ps aux | grep node
netstat -tulpn | grep LISTEN

# View PM2 logs
pm2 logs sciledger --lines 50
```

9. Nginx Setup and Configuration
```bash
# Create new SciLedger configuration
sudo tee /etc/nginx/sites-available/sciledger << 'EOF'
server {
    listen 9305;
    listen [::]:9305;
    server_name _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Remove and recreate symlink
sudo rm /etc/nginx/sites-enabled/sciledger
sudo ln -s /etc/nginx/sites-available/sciledger /etc/nginx/sites-enabled/

# Allow port in firewall
sudo ufw allow 9305/tcp

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

10. Verify Configuration
```bash
# Test local access
curl http://localhost:9305

# Test using VM IP
curl http://10.7.40.192:9305

# Test from Hungria
ssh -p 4422 leonardocabral@177.20.147.141
curl http://10.7.40.192:9305

# Test from Windows PowerShell
curl http://177.20.147.141:9305
```

11. Success Indicators
- Nginx configuration test passes
- Service restarts without errors
- curl commands return HTML content
- Application accessible through port 80
- No SSL/TLS warnings (using HTTP)

12. Troubleshooting Nginx
```bash
# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check access logs
sudo tail -f /var/log/nginx/access.log

# Verify port 80 is open
sudo ufw allow 80/tcp

# Restart Nginx after changes
sudo systemctl restart nginx
```

12. Troubleshooting Nginx Service Failures
```bash
# Check Nginx service status
sudo systemctl status nginx

# View detailed logs
journalctl -xe

# Check port availability
sudo netstat -tulpn | grep :9305

# Verify configuration
sudo nginx -t

# Check configuration files
ls -la /etc/nginx/sites-enabled/
cat /etc/nginx/sites-enabled/sciledger

# Start Nginx in debug mode
sudo nginx -t -c /etc/nginx/nginx.conf
```

12. Port Conflict Resolution
```bash
# Check what's using port 9305
sudo netstat -tulpn | grep :9305

# List all listening ports
sudo lsof -i :9305

# Kill process using port 9305 (replace PID with actual process ID)
sudo kill -9 PID

# Alternative: Change Nginx port if needed
sudo tee /etc/nginx/sites-available/sciledger << 'EOF'
server {
    listen 9306;
    listen [::]:9306;
    server_name _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Restart Nginx after fixing port conflict
sudo nginx -t
sudo systemctl restart nginx
```

13. Common Solutions
- Remove default configuration if conflicting
- Check port availability
- Verify file permissions
- Ensure proper syntax in configuration files

13. Docker Port Conflict Resolution
```bash
# Check Docker using port
sudo netstat -tulpn | grep :9305

# Stop Docker container
sudo docker stop CONTAINER_ID

# If Docker proxy persists
sudo kill $(sudo netstat -tulpn | grep :9305 | awk '{print $7}' | cut -d'/' -f1)

# Verify port is free
sudo netstat -tulpn | grep :9305

# Restart Nginx
sudo systemctl restart nginx

# Test Nginx
curl http://localhost:9305
```

15. Working Configuration
```bash
# Configuration successfully serving SvelteKit app through Nginx
# Port 9305 is working with Docker running

# Test access points
curl http://localhost:9305           # Direct VM access
curl http://10.7.40.192:9305        # Internal network access
curl http://177.20.147.141:9305     # External access through Hungria

# Verify running services
sudo netstat -tulpn | grep :9305    # Shows Docker and Nginx
sudo docker ps | grep 9305          # Shows Docker container
sudo systemctl status nginx         # Shows Nginx status
```

16. Final Configuration Notes
- Application running on port 3000 (SvelteKit)
- Nginx proxying requests from port 9305
- Docker container also using port 9305 (working together)
- MongoDB connection successful (items visible in response)
- External access through Hungria on port 9305

17. Success Indicators
```bash
# Check these indicators
- HTML response received ✓
- MongoDB items displayed ✓
- Styles loaded correctly ✓
- JavaScript loading properly ✓
- No port conflicts ✓
```

25. DNS Configuration Update
```bash
# Current DNS Resolution
scideep.imd.ufrn.br -> 10.7.40.192 (VM IP)
Previously: scideep.imd.ufrn.br -> 177.20.147.141 (Hungria IP)

# Required Changes for External Access
1. Update DNS record to point to Hungria:
   scideep.imd.ufrn.br -> 177.20.147.141

2. Configure port forwarding on Hungria:
   177.20.147.141:9305 -> 10.7.40.192:9305
```

26. DNS and Port Forwarding Request
```text
Request for Admin:

1. DNS Update Needed:
   - Domain: scideep.imd.ufrn.br
   - Current IP: 10.7.40.192
   - Required IP: 177.20.147.141
   - Purpose: Enable external access through Hungria

2. Port Forwarding:
   - External: scideep.imd.ufrn.br:9305 (177.20.147.141:9305)
   - Internal: 10.7.40.192:9305
   - Application: SciLedger web interface
```

27. HTTPS Configuration
```bash
# 1. Verify SSL certificates
ls -la /etc/nginx/certs/certificado.crt
ls -la /etc/nginx/certs/server.key

# 2. Update Nginx configuration
sudo tee /etc/nginx/sites-available/sciledger << 'EOF'
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name scideep.imd.ufrn.br;

    ssl_certificate /etc/nginx/certs/certificado.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 3. Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

28. Test HTTPS Access
```bash
# Test local HTTPS access dentro da VM
curl -k https://localhost

# Test from Hungria
curl -k https://10.7.40.192

# Test from Windows (PowerShell)
curl -k https://scideep.imd.ufrn.br

# Browser access
https://scideep.imd.ufrn.br
```

29. SSL Troubleshooting
```bash
# Check SSL certificate
openssl x509 -in /etc/nginx/certs/certificado.crt -text -noout

# Check Nginx SSL logs
sudo tail -f /var/log/nginx/error.log

# Verify SSL port is open
sudo netstat -tulpn | grep :9305

# Check SSL handshake
openssl s_client -connect localhost:9305
```

### Working HTTPS Configuration

1. SSL Setup Status ✓
```bash
# Certificate Details
- Valid until: Sep 13 16:11:04 2025 GMT
- Domain: *.imd.ufrn.br
- Issuer: GlobalSign RSA OV SSL CA 2018

# Active Ports
- HTTP: 9305
- HTTPS: 443

# Working Access Points
curl http://localhost:9305           # Local HTTP ✓
curl -k https://localhost           # Local HTTPS ✓
curl http://10.7.40.192:9305       # Internal HTTP ✓
curl -k https://10.7.40.192        # Internal HTTPS ✓
```

2. Current Infrastructure
```text
Client -> HTTPS -> Hungria (177.20.147.141) -> HTTP -> VM (10.7.40.192:9305) -> App (localhost:3000)
```

3. Next Steps
- Request port 443 forwarding on Hungria
- Update DNS records
- Implement automatic HTTP to HTTPS redirect
