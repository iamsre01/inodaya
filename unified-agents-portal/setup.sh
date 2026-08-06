#!/bin/bash

# Unified Agents Portal - Universal Setup Script
# Automatically detects project location and configures auto-sync

set -e

echo "🚀 Unified Agents Portal - Quick Setup"
echo "======================================"

# Detect project directory (parent of where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📂 Project Directory: $PROJECT_DIR"

# Get GitHub URL
if [ -z "$GITHUB_REPO_URL" ]; then
    echo ""
    echo "⚠️  GITHUB_REPO_URL environment variable not set!"
    echo ""
    echo "Please provide your GitHub repository URL:"
    echo "Example: https://github.com/yourusername/your-repo.git"
    echo ""
    read -p "Enter GitHub repository URL: " REPO_URL
else
    REPO_URL="$GITHUB_REPO_URL"
    echo "✅ Using GitHub repo: $REPO_URL"
fi

# Step 1: Configure Git Remote
echo ""
echo "📦 Step 1: Configuring Git remote..."
cd "$PROJECT_DIR"

if git remote get-url origin &>/dev/null; then
    CURRENT_URL=$(git remote get-url origin)
    if [ "$CURRENT_URL" != "$REPO_URL" ]; then
        echo "   ⚙️  Updating remote URL..."
        git remote set-url origin "$REPO_URL"
    else
        echo "   ℹ️  Git remote already configured correctly"
    fi
else
    echo "   ➕ Adding remote origin..."
    git remote add origin "$REPO_URL"
fi

# Step 2: Create Auto-Sync Script in Project Root
echo ""
echo "🔧 Step 2: Setting up auto-sync script..."

SYNC_SCRIPT="$PROJECT_DIR/auto-sync.sh"
cat > "$SYNC_SCRIPT" << EOF
#!/bin/bash

# Auto-Sync Script for Unified Agents Portal
# Location: $PROJECT_DIR

REPO_URL="$REPO_URL"
PROJECT_DIR="$PROJECT_DIR"
LOG_FILE="\$PROJECT_DIR/sync.log"
USER_NAME="$(whoami)"

log() {
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" | tee -a "\$LOG_FILE"
}

cd "\$PROJECT_DIR" || exit 1

log "Starting auto-sync check..."

# Fetch latest changes
git fetch origin main 2>&1 | tee -a "\$LOG_FILE"

# Check if local branch is behind
LOCAL=\$(git rev-parse @)
REMOTE=\$(git rev-parse @{u})

if [ "\$LOCAL" != "\$REMOTE" ]; then
    log "Changes detected! Pulling updates..."
    
    # Pull changes
    git pull origin main 2>&1 | tee -a "\$LOG_FILE"
    
    if [ \$? -eq 0 ]; then
        log "✅ Update successful."
        
        # Check if requirements.txt changed
        if git diff HEAD@{1} HEAD --quiet -- requirements.txt; then
            log "No dependency changes."
        else
            log "📦 Dependencies changed. Reinstalling..."
            if [ -d "venv" ]; then
                source venv/bin/activate
                pip install -r requirements.txt >> "\$LOG_FILE" 2>&1
            fi
        fi
        
        log "✅ Sync complete."
    else
        log "❌ Pull failed! Check conflicts."
        exit 1
    fi
else
    log "✅ Already up to date."
fi
EOF

chmod +x "$SYNC_SCRIPT"
echo "   ✅ Created auto-sync.sh at $SYNC_SCRIPT"

# Step 3: Create Systemd Service Files
echo ""
echo "🛠️  Step 3: Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/unified-agents-portal-sync.service"
TIMER_FILE="/etc/systemd/system/unified-agents-portal-sync.timer"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Unified Agents Portal Auto-Sync
After=network.target

[Service]
Type=oneshot
ExecStart=$SYNC_SCRIPT
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

sudo bash -c "cat > $TIMER_FILE" << EOF
[Unit]
Description=Run Unified Agents Portal Auto-Sync every 5 minutes
Requires=unified-agents-portal-sync.service

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=unified-agents-portal-sync.service

[Install]
WantedBy=timers.target
EOF

echo "   ✅ Created systemd service files"

# Step 4: Enable and Start Timer
echo ""
echo "⏱️  Step 4: Enabling auto-sync timer..."
sudo systemctl daemon-reload
sudo systemctl enable unified-agents-portal-sync.timer
sudo systemctl start unified-agents-portal-sync.timer

echo "   ✅ Timer enabled and started"

# Step 5: Verification
echo ""
echo "✅ Setup Complete!"
echo "=================="
echo "📍 Project Location: $PROJECT_DIR"
echo "🔄 Auto-sync interval: Every 5 minutes"
echo "📄 Log file: $PROJECT_DIR/sync.log"
echo ""
echo "Commands:"
echo "  View status:  systemctl status unified-agents-portal-sync.timer"
echo "  View logs:    tail -f $PROJECT_DIR/sync.log"
echo "  Run manually: $SYNC_SCRIPT"
echo ""
echo "🎉 Your system will now automatically sync with GitHub!"
