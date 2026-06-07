## Practice Project

I created this project to explore the opportunities in Prompt-Engineering.

Machine specs:

- i9-111900H @ 2.5Ghz (16 CPUs)
- 6GB VRAM (GeForce RTX 3060 Laptop GPU)
- 32GB RAM

### LLM Model

- Gemma4:e2b we will start the architectural design using this model then we will upgrade as the project grows.

### Main Goal

The main goal of this project is to create a reliable system architecture for agentic workflow so that it can provide less hallucinated answers, relying based on facts and realtime data.

### TODO

1. Research (RAG)
```
Instead of a general chatbot, build a system that only answers questions based on a specific set of private documents (PDFs, Markdown notes, or technical manuals).
Move beyond single prompts. Build an agent that can browse the web, summarize findings, and compile a report.
The Concept: The user provides a topic (e.g., "Hollow block cement price 2026"). The agent searches, clicks links, reads content, and writes a markdown file.
The Tech: Use LangChain or LlamaIndex with a vector database like ChromaDB or Pinecone. CrewAI or LangGraph for multi-agent orchestration. You can have one agent "Search," one "Analyze," and one "Write."
The Twist: Run the entire stack locally using Ollama or LM Studio to ensure data privacy.
Key Feature: Implement "Source Citations" where the LLM must provide the exact page or paragraph it used to generate the answer.
The Challenge: Handling "hallucinations" by making the agent cross-reference facts between different websites.
```

2. Escalation Engine Gateway
```
An agent designed to handle the client concerns initially before escalating it to real people. This agent will use the available Knowledge Base (KB) from QnA documentations and people-to-people conversations.
```
