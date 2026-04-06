## Practice Project

I created this project to explore the opportunities in Prompt-Engineering.

Machine specs:

- i9-111900H @ 2.5Ghz (16 CPUs)
- 6GB VRAM (GeForce RTX 3060 Laptop GPU)
- 32GB RAM

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

2. Structured Data Extractor (JSON Agent)
```
Most LLM usage is conversational, but their power in industry lies in converting messy text into clean, structured data.
The Concept: Create a tool where a user drops an image or text of a receipt, a medical report, or a legal contract.
The Tech: Use Pydantic to define a schema and prompt the LLM to return strictly valid JSON.
Project Goal: Build a dashboard that visualizes this extracted data (e.g., a personal finance tracker that parses receipts).
```

3. Multi-Modal Content Creator
```
Combine LLMs with other AI models to create a full content pipeline.
The Concept: Input a short story idea. The LLM writes the script, then sends prompts to a text-to-image model (like Stable Diffusion) for illustrations, and a text-to-speech model for narration.
The Result: An automated "Video Generator" or "AI Comic Book" creator.
```

4. Codebase "Janitor"
```
A tool designed specifically for developers to manage technical debt.
The Concept: Point the tool at a GitHub repository. It scans the code for missing documentation, inefficient loops, or security vulnerabilities.
The Twist: Instead of just pointing out errors, have the agent create a Pull Request with the suggested fixes.
```
