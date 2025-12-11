# Persistent MCP Server Deployment Guide

This guide explains how to deploy the Hyperliquid MCP Server as a **persistent background service** on a VPS using Docker and connect to it securely via an SSH tunnel.

## 1. VPS Setup (Docker)

**1. Install Docker**

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install docker.io -y
```

**2. Setup Project (via GitHub)**

```bash
# Clone your repository
git clone <your-github-repo-url>
cd <repo-name>

# Create .env file (Paste your keys here)
nano .env
```

**3. Run Container**
Run the server in a detached Docker container with auto-restart.

```bash
# Build
sudo docker build -t hl-mcp .

# Run (Persistent)
sudo docker run -d \
  --name hl-mcp-server \
  --restart always \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  hl-mcp python server.py --transport sse --port 8000
```

## 2. Connection Setup (Local Side)

Create a secure SSH tunnel to forward your local port 8000 to the VPS port 8000. This allows your local MCP client to talk to the remote server as if it were running locally.

### Option A: Command Line (Quickest)

Run this command in your local terminal (PowerShell, Command Prompt, or Terminal):

```bash
# Syntax: ssh -i <key> -L <local_port>:localhost:<remote_port> -N <user>@<host>
ssh -i /path/to/private_key -L 8000:localhost:8000 -N user@vps_ip
```

**Flags Explained:**

- `-L 8000:localhost:8000`: Forwards local port 8000 to `localhost:8000` on the remote server.
- `-N`: Do not execute a remote command (just forward ports).
- `-i`: Specifies the identity file (private key).

### Option B: SSH Config (Recommended)

Save your connection details to `~/.ssh/config` (Mac/Linux) or `C:\Users\YourUser\.ssh\config` (Windows) to simplify the command.

1. **Edit Config File:**

   ```text
   Host hl-mcp
       HostName vps_ip
       User user
       IdentityFile /path/to/private_key
       LocalForward 8000 localhost:8000
   ```

2. **Connect:**
   ```bash
   ssh -N hl-mcp
   ```

### Option C: Windows Users (PuTTY)

If you prefer a GUI:

1. Open PuTTY.
2. **Session**: Enter Host Name (IP address).
3. **Connection > SSH > Auth**: Browse and select your private key (`.ppk`).
4. **Connection > SSH > Tunnels**:
   - **Source port**: `8000`
   - **Destination**: `localhost:8000`
   - Click **Add**.
5. Go back to **Session**, give it a name (e.g., "Hyperliquid MCP"), and click **Save**.
6. Click **Open** to connect.

### Verifying the Connection

With the SSH tunnel running, open your browser or use `curl` locally:

```bash
curl http://localhost:8000/sse
```

You should see a response (likely a 404 or method not allowed, but _not_ a "Connection Refused" error), indicating the tunnel is active.

> [!TIP] > **Auto-Reconnection**: SSH connections can drop.
>
> - **Mac/Linux**: Use `autossh -M 0 -f -N hl-mcp` to automatically restart the tunnel.
> - **Windows**: Configure PuTTY **Connection > Sending of null packets to keep session active** to `10` seconds.

## 3. Agent Configuration

Configure your MCP client to connect to the **local** end of the tunnel.

**Config File:** `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hyperliquid-persistent": {
      "command": "",
      "url": "http://localhost:8000/sse",
      "env": {}
    }
  }
}
```

**Authentication:**
The security is handled by your **Local SSH Key**.

- The server is not exposed to the internet (only localhost).
- You authenticate to the VPS using your SSH key when creating the tunnel (specified via `-i` flag or your SSH config).
- The Agent simply connects to `localhost`, which is securely piped to the VPS.
