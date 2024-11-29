#!/bin/bash

# System configuration and utility functions
# Provides common system management operations

# Global configuration
BACKUP_DIR="/var/backups"
LOG_FILE="/var/log/system_utils.log"
MAX_BACKUPS=5

# Source common utilities
source ./common/logging.sh
. ./common/config.sh

# Set up common aliases
alias ll='ls -la'
alias df='df -h'
alias free='free -m'

# Log management function
# Parameters:
#   $1 - Log file path
#   $2 - Max size in MB
function manage_logs() {
    local log_file="$1"
    local max_size="$2"
    
    # Get current size in MB
    local current_size=$(du -m "$log_file" | cut -f1)
    
    if [ "$current_size" -gt "$max_size" ]; then
        # Rotate log file
        mv "$log_file" "${log_file}.old"
        touch "$log_file"
        echo "Log rotated at $(date)" >> "$log_file"
    fi
}

# Create system backup
# Usage: create_backup [directory]
function create_backup() {
    local target_dir=${1:-"/etc"}
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/backup_${timestamp}.tar.gz"
    
    # Create backup
    tar -czf "$backup_file" "$target_dir" || {
        echo "Backup failed"
        return 1
    }
    
    # Cleanup old backups
    cleanup_old_backups
}

# Cleanup old backup files
function cleanup_old_backups() {
    # Find and delete old backups
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f | \
        sort -r | \
        tail -n +$((MAX_BACKUPS + 1)) | \
        xargs rm -f
}

# System health check
function check_system_health() {
    # Check disk space
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    # Check memory
    local mem_free=$(free -m | awk 'NR==2 {print $4}')
    
    # Check load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | cut -d, -f1)
    
    # Print results
    cat << EOF
System Health Report
-------------------
Disk Usage: ${disk_usage}%
Free Memory: ${mem_free}MB
Load Average: ${load_avg}
EOF
}

# Initialize system
function init_system() {
    # Create necessary directories
    mkdir -p "$BACKUP_DIR"
    
    # Set up initial log file
    touch "$LOG_FILE"
    
    # Set permissions
    chmod 750 "$BACKUP_DIR"
    chmod 640 "$LOG_FILE"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    init_system
    check_system_health
fi
