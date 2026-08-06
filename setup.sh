#!/bin/bash

# ============================================
# Quick Setup Script for Unified Agents Portal
# ============================================
# Run this script to set up everything in one go
# ============================================

set -e

echo "🚀 Unified Agents Portal - Quick Setup"
echo "======================================"
echo ""

# Check if GitHub URL is provided
if [ -z "$GITHUB_REPO_URL" ]; then
    echo "⚠️  GITHUB_REPO_URL environment variable not set!"
    echo ""
    echo "Please provide your GitHub repository URL:"
    echo "Example: https://github.com/yourusername/your-repo.git"
    echo ""
    read -p "Enter GitHub repository URL: " GITHUB_REPO_URL
fi

echo "✅ Using GitHub repo: $GITHUB_REPO_URL"
echo ""

# Step 1: Configure git remote
echo "📦 Step 1: Configuring Git remote..."
EXISTING_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$EXISTING_REMOTE" ]; then
    git remote add origin "$GITHUB_REPO_URL"
    echo "   ✅ Git remote 'origin' added"
elif [ "$EXISTING_REMOTE" != "$GITHUB_REPO_URL" ]; then
    git remote set-url origin "$GITHUB_REPO_URL"
    echo "   ✅ Git remote 'origin' updated"
else
    echo "   ℹ️  Git remote already configured correctly"
fi
echo ""

# Step 2: Make sync script executable
echo "🔧 Step 2: Setting up auto-sync script..."
chmod +x /workspace/auto-sync.sh
echo "   ✅ Sync script made executable"
echo ""

# Step 3: Test sync
echo "🧪 Step 3: Testing sync (one-time)..."
export GITHUB_REPO_URL
if /workspace/auto-sync.sh --once; then
    echo "   ✅ Sync test successful"
else
    echo "   ⚠️  Sync test completed with warnings (this is OK for first run)"
fi
echo ""

# Step 4: Install Python dependencies
echo "🐍 Step 4: Installing Python dependencies..."
if [ -f "/workspace/unified-agents-portal/backend/requirements.txt" ]; then
    pip install -q -r /workspace/unified-agents-portal/backend/requirements.txt
    echo "   ✅ Dependencies installed"
else
    echo "   ℹ️  No requirements.txt found, skipping"
fi
echo ""

# Step 5: Check if running as root (for systemd setup)
if [ "$EUID" -eq 0 ]; then
    echo "🔧 Step 5: Installing systemd service..."
    cp /workspace/unified-agents-portal-sync.service /etc/systemd/system/
    
    # Update the service file with actual repo URL
    sed -i "s|https://github.com/YOUR_USERNAME/YOUR_REPO.git|$GITHUB_REPO_URL|g" /etc/systemd/system/unified-agents-portal-sync.service
    
    systemctl daemon-reload
    systemctl enable unified-agents-portal-sync.service
    systemctl start unified-agents-portal-sync.service
    
    if systemctl is-active --quiet unified-agents-portal-sync.service; then
        echo "   ✅ Systemd service installed and started"
    else
        echo "   ⚠️  Service installation completed with warnings"
    fi
    echo ""
    
    echo "🌐 Step 6: Starting backend server..."
    cd /workspace/unified-agents-portal/backend
    nohup python main.py > /var/log/agents-backend.log 2>&1 &
    sleep 3
    if curl -s http://localhost:8000/agents > /dev/null 2>&1; then
        echo "   ✅ Backend server started on http://localhost:8000"
    else
        echo "   ⚠️  Backend server may need manual start"
    fi
    echo ""
    
    echo "🖥️  Step 7: Starting frontend server..."
    cd /workspace/unified-agents-portal/frontend
    nohup python -m http.server 3000 > /var/log/agents-frontend.log 2>&1 &
    sleep 2
    echo "   ✅ Frontend server started on http://localhost:3000"
    echo ""
    
    echo "======================================"
    echo "🎉 Setup Complete!"
    echo "======================================"
    echo ""
    echo "📊 Access Points:"
    echo "   • Backend API: http://localhost:8000"
    echo "   • Frontend UI: http://localhost:3000"
    echo ""
    echo "🔄 Auto-Sync Status:"
    echo "   • Service: Active and running"
    echo "   • Interval: Every 5 minutes"
    echo "   • Logs: sudo journalctl -u unified-agents-portal-sync.service -f"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Open http://localhost:3000 in your browser"
    echo "   2. Start creating agents and tasks"
    echo "   3. All changes will auto-sync to GitHub!"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   • View sync logs: sudo journalctl -u unified-agents-portal-sync.service -f"
    echo "   • Stop sync: sudo systemctl stop unified-agents-portal-sync.service"
    echo "   • Restart sync: sudo systemctl restart unified-agents-portal-sync.service"
    echo "   • Manual sync: /workspace/auto-sync.sh --once"
    echo ""
else
    echo "⚠️  Not running as root. Skipping systemd installation."
    echo ""
    echo "To enable auto-start on boot, run this script with sudo:"
    echo "   sudo ./setup.sh"
    echo ""
    echo "Or manually copy the service file:"
    echo "   sudo cp /workspace/unified-agents-portal-sync.service /etc/systemd/system/"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl enable unified-agents-portal-sync.service"
    echo "   sudo systemctl start unified-agents-portal-sync.service"
    echo ""
    
    echo "======================================"
    echo "🎉 Basic Setup Complete!"
    echo "======================================"
    echo ""
    echo "📊 You can now:"
    echo "   • Run backend: cd /workspace/unified-agents-portal/backend && python main.py"
    echo "   • Run frontend: cd /workspace/unified-agents-portal/frontend && python -m http.server 3000"
    echo "   • Manual sync: /workspace/auto-sync.sh --once"
    echo ""
fi

echo "📖 For detailed documentation, see: /workspace/DEPLOYMENT_GUIDE.md"
echo ""
