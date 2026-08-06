# Unified Agents Control Portal - Deployment & Auto-Sync Guide

## 🚀 Complete Setup Guide for Automated GitHub Sync

This guide will help you:
1. Set up the project on a new machine
2. Configure automatic synchronization with GitHub
3. Deploy the application with zero manual intervention

---

## 📋 Prerequisites

- Linux/Unix-based system (Ubuntu, Debian, macOS, etc.)
- Git installed (`git --version`)
- Python 3.8+ installed (`python3 --version`)
- A GitHub account and repository
- SSH keys or GitHub Personal Access Token for authentication

---

## 🔧 Step 1: Clone Your Repository

```bash
# Clone your repository to /workspace (or your preferred directory)
cd /home/your-user
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git workspace
cd workspace

# Or if using SSH (recommended)
git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git workspace
cd workspace
```

---

## 🔑 Step 2: Configure Git Authentication

### Option A: SSH Keys (Recommended)

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add SSH key to GitHub
# 1. Copy the public key
cat ~/.ssh/id_ed25519.pub

# 2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
# 3. Paste the key and save

# Test connection
ssh -T git@github.com
```

### Option B: Personal Access Token

```bash
# Create token at: https://github.com/settings/tokens
# Scopes needed: repo, workflow

# Configure git to use token
git config --global credential.helper store

# Next time you push, it will ask for credentials once and remember them
```

---

## ⚙️ Step 3: Configure Auto-Sync Script

### 3.1 Make the script executable

```bash
chmod +x /workspace/auto-sync.sh
```

### 3.2 Set your GitHub repository URL

Edit the systemd service file or set environment variable:

**Method 1: Edit systemd service file (Recommended for production)**

```bash
sudo nano /workspace/unified-agents-portal-sync.service
```

Update this line with your actual GitHub repo URL:
```ini
Environment="GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/YOUR_REPO.git"
```

Or for SSH:
```ini
Environment="GITHUB_REPO_URL=git@github.com:YOUR_USERNAME/YOUR_REPO.git"
```

**Method 2: Set as environment variable**

```bash
export GITHUB_REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git"
```

### 3.3 Test the sync script manually first

```bash
# Run once to test
/workspace/auto-sync.sh --once

# Or with environment variable
GITHUB_REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git" /workspace/auto-sync.sh --once
```

Expected output:
```
[INFO] Using GitHub repo: https://github.com/YOUR_USERNAME/YOUR_REPO.git
[INFO] Starting sync cycle...
[INFO] Pulling latest changes from GitHub...
[SUCCESS] Successfully pulled latest changes
[INFO] No changes detected. Workspace is up to date.
```

---

## 🖥️ Step 4: Install as Systemd Service (Linux)

This enables automatic syncing even after reboot.

### 4.1 Copy service file to systemd directory

```bash
sudo cp /workspace/unified-agents-portal-sync.service /etc/systemd/system/
```

### 4.2 Reload systemd daemon

```bash
sudo systemctl daemon-reload
```

### 4.3 Enable and start the service

```bash
# Enable to start on boot
sudo systemctl enable unified-agents-portal-sync.service

# Start the service now
sudo systemctl start unified-agents-portal-sync.service

# Check status
sudo systemctl status unified-agents-portal-sync.service
```

### 4.4 View logs

```bash
# Real-time logs
sudo journalctl -u unified-agents-portal-sync.service -f

# Last 50 lines
sudo journalctl -u unified-agents-portal-sync.service -n 50
```

### 4.5 Service management commands

```bash
# Stop service
sudo systemctl stop unified-agents-portal-sync.service

# Restart service
sudo systemctl restart unified-agents-portal-sync.service

# Disable auto-start on boot
sudo systemctl disable unified-agents-portal-sync.service
```

---

## 🍎 Alternative: macOS LaunchAgent

If you're on macOS, use LaunchAgent instead of systemd.

### 4.1 Create LaunchAgent plist

Create `/workspace/com.unified-agents.sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.unified-agents.sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/workspace/auto-sync.sh</string>
        <string>--continuous</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/workspace</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>GITHUB_REPO_URL</key>
        <string>https://github.com/YOUR_USERNAME/YOUR_REPO.git</string>
        <key>SYNC_INTERVAL</key>
        <string>300</string>
    </dict>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/tmp/agents-sync.out</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/agents-sync.err</string>
</dict>
</plist>
```

### 4.2 Load the LaunchAgent

```bash
# Copy to LaunchAgents
cp /workspace/com.unified-agents.sync.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.unified-agents.sync.plist

# Check status
launchctl list | grep agents-sync

# Unload if needed
launchctl unload ~/Library/LaunchAgents/com.unified-agents.sync.plist
```

---

## 🐳 Alternative: Docker Deployment

For containerized deployment with auto-sync.

### 5.1 Create Dockerfile

Create `/workspace/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Install git and dependencies
RUN apt-get update && apt-get install -y \
    git \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install fastapi uvicorn sqlalchemy apscheduler pydantic

# Make sync script executable
RUN chmod +x /workspace/auto-sync.sh

# Expose ports
EXPOSE 8000 3000

# Start backend and sync service
CMD ["sh", "-c", "python unified-agents-portal/backend/main.py & /workspace/auto-sync.sh --continuous"]
```

### 5.2 Build and run

```bash
# Build image
docker build -t unified-agents-portal .

# Run container
docker run -d \
  -e GITHUB_REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git" \
  -e SYNC_INTERVAL="300" \
  -p 8000:8000 \
  -p 3000:3000 \
  --name agents-portal \
  unified-agents-portal

# View logs
docker logs -f agents-portal
```

---

## ⏱️ Step 5: Alternative - Cron Job Setup

If you prefer cron over systemd:

### 5.1 Edit crontab

```bash
crontab -e
```

### 5.2 Add cron entry (sync every 5 minutes)

```bash
*/5 * * * * cd /workspace && /workspace/auto-sync.sh --once >> /var/log/agents-sync.log 2>&1
```

### 5.3 View cron logs

```bash
tail -f /var/log/agents-sync.log
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Git remote is configured: `git remote -v`
- [ ] Manual sync works: `/workspace/auto-sync.sh --once`
- [ ] Service is running: `sudo systemctl status unified-agents-portal-sync.service`
- [ ] Logs show successful syncs: `sudo journalctl -u unified-agents-portal-sync.service`
- [ ] Changes in workspace appear on GitHub
- [ ] Changes from GitHub pull to workspace automatically
- [ ] Backend server is running: `curl http://localhost:8000/agents`
- [ ] Frontend is accessible: Open browser to http://localhost:3000

---

## 🔍 Troubleshooting

### Issue: Authentication failed

**Solution:**
```bash
# For SSH, ensure key is added to ssh-agent
ssh-add ~/.ssh/id_ed25519

# For HTTPS, clear stored credentials and re-enter
git credential reject
# Then try pushing again
```

### Issue: Service won't start

**Solution:**
```bash
# Check detailed error
sudo journalctl -u unified-agents-portal-sync.service -n 50 --no-pager

# Test script manually
sudo /workspace/auto-sync.sh --once

# Check file permissions
ls -la /workspace/auto-sync.sh
chmod +x /workspace/auto-sync.sh
```

### Issue: Conflicts during sync

**Solution:**
The script uses `--rebase --autostash` to handle conflicts automatically. If conflicts persist:

```bash
cd /workspace
git status
# Resolve conflicts manually
git add .
git commit -m "Resolve merge conflicts"
git push
```

### Issue: Service starts before network is ready

**Solution:**
The systemd service already includes `After=network.target`. If issues persist, add:

```ini
[Service]
ExecStartPre=/bin/sleep 10
```

---

## 📊 Monitoring & Maintenance

### Check sync status anytime

```bash
# Last 10 sync attempts
sudo journalctl -u unified-agents-portal-sync.service -n 10

# Count successful syncs today
sudo journalctl -u unified-agents-portal-sync.service --since today | grep -c "SUCCESS"
```

### Adjust sync frequency

Edit the service file:
```bash
sudo nano /etc/systemd/system/unified-agents-portal-sync.service
```

Change:
```ini
Environment="SYNC_INTERVAL=60"  # Sync every minute
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart unified-agents-portal-sync.service
```

### Temporary pause

```bash
sudo systemctl stop unified-agents-portal-sync.service
```

### Resume syncing

```bash
sudo systemctl start unified-agents-portal-sync.service
```

---

## 🎯 Quick Start Commands Summary

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /workspace
cd /workspace

# 2. Install dependencies
pip install -r unified-agents-portal/backend/requirements.txt

# 3. Configure GitHub URL
export GITHUB_REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git"

# 4. Test sync
./auto-sync.sh --once

# 5. Install systemd service
sudo cp unified-agents-portal-sync.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable unified-agents-portal-sync.service
sudo systemctl start unified-agents-portal-sync.service

# 6. Start backend
cd unified-agents-portal/backend
python main.py &

# 7. Start frontend
cd ../frontend
python -m http.server 3000 &

# 8. Verify
curl http://localhost:8000/agents
```

---

## 🎉 You're Done!

Your Unified Agents Control Portal is now:
- ✅ Running on your machine
- ✅ Automatically syncing with GitHub every 5 minutes
- ✅ Configured to survive reboots
- ✅ Logging all sync activities
- ✅ Ready for zero-maintenance operation

Any changes you make in the workspace will automatically commit and push to GitHub. Any changes from other team members will automatically pull into your workspace.

**No manual validation needed!** 🚀
