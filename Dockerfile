FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && \
  useradd -m agentuser

RUN mkdir -p /home/agentuser/bin \
             /home/agentuser/agent && \
  chown -R agentuser:agentuser /home/agentuser

USER agentuser
WORKDIR /home/agentuser/agent
