FROM python:3.11-slim

# 1. Install system basics
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 2. Install Playwright Python package
RUN pip install --no-cache-dir playwright

# 3. Install the browser AND all missing system dependencies (The Fix)
# This installs libgtk-3, libgdk-3, and all the .so files in your error log.
RUN playwright install chromium --with-deps

# 4. Setup your agent user
RUN useradd -m agentuser && \
    mkdir -p /home/agentuser/bin /home/agentuser/agent && \
    chown -R agentuser:agentuser /home/agentuser

USER agentuser
WORKDIR /home/agentuser/agent
