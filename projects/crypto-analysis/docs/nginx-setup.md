# Nginx Setup for Crypto Pattern Charts

## Overview
Nginx has been configured to serve the crypto pattern charts as a static website.

## Configuration Details

### Server Information
- **Listen Port:** 8080
- **Server IP:** 10.184.169.241
- **Access URL:** http://10.184.169.241:8080
- **Root Directory:** `/root/.openclaw/workspace/projects/crypto-analysis/charts/`
- **Index File:** `index.html`

### Nginx Configuration File
**Location:** `/etc/nginx/sites-available/crypto-charts`

```nginx
server {
    listen 8080;
    server_name _;
    
    root /root/.openclaw/workspace/projects/crypto-analysis/charts/;
    index index.html;
    
    # Enable autoindex for directory browsing
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    
    # MIME types are included from /etc/nginx/mime.types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Service Management

### Check Status
```bash
systemctl status nginx
```

### Start Nginx
```bash
systemctl start nginx
# or
/usr/sbin/nginx
```

### Stop Nginx
```bash
systemctl stop nginx
# or
/usr/sbin/nginx -s stop
```

### Restart Nginx
```bash
systemctl restart nginx
# or
/usr/sbin/nginx -s restart
```

### Reload Configuration (no downtime)
```bash
/usr/sbin/nginx -s reload
```

### Test Configuration
```bash
/usr/sbin/nginx -t
```

## Files Served

The following chart files are available:

### BTCUSDT
- BTCUSDT_1M.html
- BTCUSDT_1w.html
- BTCUSDT_1d.html
- BTCUSDT_4h.html
- BTCUSDT_1h.html

### ETHUSDT
- ETHUSDT_1M.html
- ETHUSDT_1w.html
- ETHUSDT_1d.html
- ETHUSDT_4h.html
- ETHUSDT_1h.html

### BNBUSDT
- BNBUSDT_1M.html
- BNBUSDT_1w.html
- BNBUSDT_1d.html
- BNBUSDT_4h.html
- BNBUSDT_1h.html

## Features Enabled

- **Autoindex:** Directory browsing enabled for easy navigation
- **Gzip Compression:** Enabled for faster content delivery
- **Static Asset Caching:** 1-day cache for JS, CSS, images, and fonts
- **Proper MIME Types:** All standard web MIME types configured

## Troubleshooting

### Permission Issues
Nginx is configured to run as `root` user to access files in `/root/.openclaw/workspace/`.
If you change this, ensure the `www-data` user has read access to the charts directory.

### Port Conflicts
If port 8080 is already in use, you can change the listen port in:
`/etc/nginx/sites-available/crypto-charts`

Then reload Nginx:
```bash
/usr/sbin/nginx -s reload
```

### Check Logs
```bash
# Error logs
tail -f /var/log/nginx/error.log

# Access logs
tail -f /var/log/nginx/access.log
```

## Setup Date
2026-02-27

## Notes
- The default Nginx site has been disabled to avoid conflicts
- Configuration is symlinked from `sites-available` to `sites-enabled`
- All HTML chart files are interactive and fully functional
