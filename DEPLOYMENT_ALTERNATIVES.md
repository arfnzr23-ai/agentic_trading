# 🚀 Alternative Deployment Options

In addition to the manual setup described in `DEPLOYMENT.md`, we provide two "Quick Deploy" alternatives:

1. **Docker Compose (Recommended)**: Best for reliability, isolation, and quick updates.
2. **One-Click Script**: Best for bare-metal VPS if you prefer not to use Docker.

---

## Option 1: Docker Compose (Speed & Isolation)

This method runs the MCP Server, the Trading Agent, and the Dashboard as managed containers.

### Prerequisites

- Docker & Docker Compose installed on your VPS.

### Steps

1. **Clone & Configure**

   ```bash
   git clone https://github.com/your-repo/hyperliquid-mcp-agent.git
   cd hyperliquid-mcp-agent
   cp .env.example .env
   nano .env  # Enter your keys!
   ```

2. **Start Everything**

   ```bash
   docker compose up -d
   ```

   _This builds the images and starts the server (port 8000), agent (background), and dashboard (port 8501)._

3. **Access**
   - **Dashboard**: `http://your-vps-ip:8501`
   - **Logs**: `docker compose logs -f`

### Stopping/Updating

- Stop: `docker compose down`
- Update: `git pull && docker compose up -d --build`

---

## Option 2: One-Click VPS Script (Simple)

This script automates the "Detailed Setup" from the main guide. It installs Python, Node.js, sets up the virtual environment, and creates systemd services.

### Steps

1. **Upload & Run**

   ```bash
   # Download the script (or create it)
   curl -O https://raw.githubusercontent.com/your-repo/hyperliquid-mcp-agent/main/scripts/setup_vps.sh

   # Make executable
   chmod +x setup_vps.sh

   # Run
   ./setup_vps.sh
   ```

2. **Configure**
   The script will pause to let you edit `.env`.

3. **Verify**
   ```bash
   sudo systemctl status hl-agent
   ```

---

## Comparison

| Feature        | Docker Compose              | One-Click Script               | Manual Setup |
| -------------- | --------------------------- | ------------------------------ | ------------ |
| **Setup Time** | ~2 mins                     | ~5 mins                        | ~15 mins     |
| **Updates**    | `docker compose up --build` | `git pull && restart services` | Manual       |
| **Isolation**  | High (Containers)           | Low (System Python)            | Low          |
| **Complexity** | Low                         | Low                            | High         |
