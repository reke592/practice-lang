FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/* && \
  useradd -m agentuser

RUN mkdir -p /home/agentuser/bin /home/agentuser/agent/venv && \
    chown -R agentuser:agentuser /home/agentuser

USER agentuser
WORKDIR /home/agentuser/agent

RUN mkdir -p var \
    mkdir -p tmp
