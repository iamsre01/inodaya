#!/bin/bash

# ============================================
# Unified Agents Portal - Auto Sync Script
# ============================================
# This script automatically:
# 1. Detects file changes in the workspace
# 2. Commits changes to Git
# 3. Pushes to GitHub remote
# 4. Pulls latest changes from GitHub
# ============================================

set -e  # Exit on error

# Configuration
GITHUB_REPO_URL="${GITHUB_REPO_URL:-}"  # Set your GitHub repo URL here or as env var
SYNC_INTERVAL="${SYNC_INTERVAL:-300}"   # Sync every 5 minutes (default)
WORKSPACE_DIR="/workspace"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if GitHub repo URL is configured
check_github_config() {
    if [ -z "$GITHUB_REPO_URL" ]; then
        EXISTING_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
        if [ -z "$EXISTING_REMOTE" ]; then
            log_error "GitHub repository URL not configured!"
            log_warning "Please set GITHUB_REPO_URL environment variable or configure git remote:"
            log_warning "  git remote add origin <your-github-repo-url>"
            return 1
        fi
        GITHUB_REPO_URL="$EXISTING_REMOTE"
        log_info "Using existing remote: $GITHUB_REPO_URL"
    else
        log_info "Using GitHub repo: $GITHUB_REPO_URL"
    fi
    return 0
}

# Setup git remote if not exists
setup_git_remote() {
    if [ -n "$GITHUB_REPO_URL" ]; then
        EXISTING_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
        if [ -z "$EXISTING_REMOTE" ]; then
            log_info "Setting up git remote origin..."
            git remote add origin "$GITHUB_REPO_URL"
            log_success "Git remote configured successfully"
        elif [ "$EXISTING_REMOTE" != "$GITHUB_REPO_URL" ]; then
            log_warning "Remote URL mismatch. Updating..."
            git remote set-url origin "$GITHUB_REPO_URL"
            log_success "Git remote updated successfully"
        fi
    fi
}

# Perform one sync cycle
sync_once() {
    cd "$WORKSPACE_DIR"
    
    log_info "Starting sync cycle..."
    
    # Pull latest changes first (to avoid conflicts)
    log_info "Pulling latest changes from GitHub..."
    if git pull --rebase --autostash origin "$(git branch --show-current)" 2>/dev/null; then
        log_success "Successfully pulled latest changes"
    else
        log_warning "Pull failed or no remote configured. Continuing with commit..."
    fi
    
    # Check for changes
    CHANGES=$(git status --porcelain)
    
    if [ -z "$CHANGES" ]; then
        log_info "No changes detected. Workspace is up to date."
        return 0
    fi
    
    log_info "Changes detected:"
    echo "$CHANGES"
    
    # Stage all changes
    log_info "Staging all changes..."
    git add -A
    
    # Commit changes
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    COMMIT_MSG="Auto-sync: Changes detected at $TIMESTAMP"
    
    log_info "Committing changes..."
    if git commit -m "$COMMIT_MSG"; then
        log_success "Changes committed successfully"
    else
        log_warning "Nothing to commit or commit failed"
        return 0
    fi
    
    # Push to GitHub
    if [ -n "$GITHUB_REPO_URL" ]; then
        log_info "Pushing changes to GitHub..."
        if git push origin "$(git branch --show-current)"; then
            log_success "Changes pushed to GitHub successfully"
        else
            log_error "Failed to push to GitHub. Please check credentials and remote URL."
            return 1
        fi
    else
        log_warning "No GitHub remote configured. Skipping push."
    fi
    
    return 0
}

# Continuous sync loop
sync_continuous() {
    log_info "Starting continuous sync (interval: ${SYNC_INTERVAL}s)"
    log_info "Press Ctrl+C to stop"
    
    while true; do
        sync_once
        sleep "$SYNC_INTERVAL"
    done
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --once        Run sync once and exit"
    echo "  --continuous  Run sync continuously (default)"
    echo "  --interval N  Set sync interval in seconds (default: 300)"
    echo "  --setup       Only setup git remote, don't sync"
    echo "  --help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_REPO_URL  Your GitHub repository URL"
    echo "  SYNC_INTERVAL    Sync interval in seconds"
    echo ""
    echo "Examples:"
    echo "  $0 --once"
    echo "  GITHUB_REPO_URL=https://github.com/user/repo.git $0 --continuous"
    echo "  SYNC_INTERVAL=60 $0 --once"
}

# Main execution
main() {
    case "${1:-}" in
        --once)
            check_github_config || exit 1
            setup_git_remote
            sync_once
            ;;
        --setup)
            check_github_config || exit 1
            setup_git_remote
            log_success "Git remote setup complete"
            ;;
        --continuous)
            check_github_config || exit 1
            setup_git_remote
            sync_continuous
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            # Default: run once
            check_github_config || exit 1
            setup_git_remote
            sync_once
            ;;
    esac
}

main "$@"
