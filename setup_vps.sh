#!/bin/bash

# One-Click Setup Script for Hyperliquid MCP Agent
# Run this on a fresh Ubuntu 22.04+ VPS

set -e

echo "=================================================="
echo "   Hyperliquid MCP Agent - Auto Installer"
echo "=================================================="

# 1. Check Root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (or use sudo)"
  exit 1
fi

# 2. System Updates
echo "[1/6] Updating system..."
apt-get update && apt-get upgrade -y
apt-get install -y python3.11 python3.11-venv python3-pip git tmux curl ufw

# 3. Setup Project Directory
# Assuming script is run from inside the repo folder
WORK_DIR=$(pwd)
echo "[2/6] Setting up in $WORK_DIR..."

if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  PLEASE EDIT .env NOW! The script will pause."
        echo "Press ENTER after you have edited .env with your keys."
        read -p "Press [Enter] key to continue..."
    else
        echo "Error: .env.example not found!"
        exit 1
    fi
fi

# 4. Python Environment
echo "[3/6] Setting up Python dependencies..."
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate

# Install Core dependencies
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Install Sub-module dependencies
if [ -f "deployment-test/requirements.txt" ]; then
    pip install -r deployment-test/requirements.txt
fi
if [ -f "agent/requirements.txt" ]; then
    pip install -r agent/requirements.txt
fi

# 5. Dashboard (Streamlit)
echo "[4/6] Installing Streamlit..."
# Already in requirements, but ensuring it's accessible
# pip install streamlit

# 6. Systemd Services
echo "[5/6] Creating Systemd Services..."

# Path adjustments
VENV_PYTHON="$WORK_DIR/venv/bin/python"
MCP_SERVER_SCRIPT="$WORK_DIR/deployment-test/server.py"

# Service 1: MCP Server
cat > /etc/systemd/system/hl-mcp.service <<EOF
[Unit]
Description=Hyperliquid MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
Environment="PYTHONUNBUFFERED=1"
ExecStart=$VENV_PYTHON $MCP_SERVER_SCRIPT --transport sse --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service 2: Trading Agent
cat > /etc/systemd/system/hl-agent.service <<EOF
[Unit]
Description=Hyperliquid Trading Agent
After=hl-mcp.service
Requires=hl-mcp.service

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
Environment="MCP_SERVER_URL=http://localhost:8000/sse"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$VENV_PYTHON -m agent.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service 3: Dashboard
cat > /etc/systemd/system/hl-dashboard.service <<EOF
[Unit]
Description=Hyperliquid Agent Dashboard
After=hl-agent.service

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/streamlit run ui/dashboard.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hl-mcp hl-agent hl-dashboard

# 7. Start
echo "[6/6] Starting Services..."
systemctl start hl-mcp
systemctl start hl-agent
systemctl start hl-dashboard

echo "=================================================="
echo "   ✅ Deployment Complete!"
echo "=================================================="
echo "Status:"
systemctl status hl-agent --no-pager
echo ""
echo "Dashboard: http://$(curl -s ifconfig.me):8501"
echo "Logs: journalctl -u hl-agent -f"
