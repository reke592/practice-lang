# Workspace Preparation

This section guides how to setup the development environment.

### 1. Download and Install the required Softwares

- [Ollama](https://ollama.com/download) Open source LLM runner. (For local testing only) -- we use [vLLM](https://docs.vllm.ai/en/latest/) for production deployments.

- Docker [Windows](https://docs.docker.com/desktop/setup/install/windows-install/) or [Ubuntu](https://docs.docker.com/engine/install/ubuntu/) for the Development Container.

### 2. Ollama Server Preparation

- Pull the Ollama models we needed for this notebook.

```sh
# the LLM
ollama pull gemma4:e2b

# the embedding model for the RAG
ollama pull nomic-embed-text-v2-moe
```

- Run the Ollama server manually in CMD. (stop the ollama in windows icon tray first before running the below commands)

```sh
# this command will start the server in http://localhost:11434 of the host machine. 
# To access the server inside the docker container on windows, we will use host.docker.internal instead of localhost. http://host.docker.internal:11434
ollama serve
```

### 3. Development Container Preparation

#### 3.1 Create `Dockerfile` and save the following content.

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/* && \
  useradd -m agentuser

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
```

#### 3.2 Create a `docker-compose.yml` and save the following content.

```yml
services:
  dev:
    build:
      dockerfile: Dockerfile
      context: .
    volumes:
      - ./:/home/agentuser/agent
    command: tail -f /dev/null
    network_mode: host
```

#### 3.3 Run the Development container.

```sh
docker compose up -d
```

### 4. Using the Development Container

#### 4.1 Open VSCode and attach to running container.

- press `ctrl+shift+P` and type in search `dev att`

#### 4.2 Create python virtual environment `venv` inside the container and install the required packages.

```sh
# run this command only once to create new virtual environment
python -m venv venv

# activate the environment
. ./venv/bin/activate

# install the packages
pip install langchain langgraph langchain_openai langchain_ollama

# freeze the package requirements so that we can re-install / upgrade later
pip freeze > requirements.txt

# to re-install
pip install -r requirements.txt

# to upgrade all
pip install -U -r requirements.txt
```