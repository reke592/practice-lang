from typing import Literal
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

import environment as env

def init_llm(model: str, 
             provider: Literal["google","ollama","openai"], 
             reasoning: bool = False, 
             temperature: float = 0,
             thinking_level: Literal["low","medium", "high"]="high"):
  if provider=="ollama":
    return ChatOllama(
      model=model,
      base_url=env.LLM_PROVIDER_BASE_URL,
      temperature=temperature,
      reasoning=reasoning,
    )
  # TODO: fix registry
  if provider=="openai":
    return ChatOpenAI(
      model=model,
      base_url=env.LLM_PROVIDER_BASE_URL,
      api_key=env.LLM_PROVIDER_API_KEY,
      temperature=temperature,
      reasoning={
        'effort': thinking_level,
      },
      extra_body={
        "tool_choice": "auto", # Explicitly tell vLLM to expect tools
        "multimodal_max_images": 3,
        "chat_template_kwargs": {
          "enable_thinking": False
        }
      }
    )
  raise ValueError("Invalid arguments.")


PROVIDERS = {
  'qwen2.5': {
    'FAST': init_llm(provider="ollama", model="qwen2.5-coder:3b", thinking_level="low", reasoning=False),
    'BALANCED': init_llm(provider="ollama", model="qwen2.5-coder:3b", thinking_level="medium", reasoning=True),
    'PRECISE': init_llm(provider="ollama", model="qwen2.5-coder:3b", thinking_level="high", reasoning=True),
  },
  'qwen3:4b': {
    'FAST': init_llm(provider="ollama", model="qwen3:4b", thinking_level="low", reasoning=False),
    'BALANCED': init_llm(provider="ollama", model="qwen3:4b", thinking_level="medium", reasoning=True),
    'PRECISE': init_llm(provider="ollama", model="qwen3:4b", thinking_level="high", reasoning=True),
  },
  'qwen3.5:2b': {
    'FAST': init_llm(provider="ollama", model="qwen3.5:2b", thinking_level="low", reasoning=False),
    'BALANCED': init_llm(provider="ollama", model="qwen3.5:2b", thinking_level="medium", reasoning=True),
    'PRECISE': init_llm(provider="ollama", model="qwen3.5:2b", thinking_level="high", reasoning=True),
  },
  'qwen3.5:4b': {
    'FAST': init_llm(provider="ollama", model="qwen3.5:4b", thinking_level="low", reasoning=False),
    'BALANCED': init_llm(provider="ollama", model="qwen3.5:4b", thinking_level="medium", reasoning=True),
    'PRECISE': init_llm(provider="ollama", model="qwen3.5:4b", thinking_level="high", reasoning=True),
  },
  # 'gemini': {
  #   'FAST': init_llm(provider="google", model="gemini-3.1-flash-lite-preview", thinking_level="low"),
  #   'BALANCED': init_llm(provider="google", model="gemini-3.1-flash-lite-preview", thinking_level="medium"),
  #   'PRECISE': init_llm(provider="google", model="gemini-3.1-flash-lite-preview", thinking_level="high"),
  # },
  'gemma4:e2b': {
    'FAST': init_llm(provider="ollama", model="gemma4:e2b", thinking_level="low", reasoning=False),
    'BALANCED': init_llm(provider="ollama", model="gemma4:e2b", thinking_level="medium", reasoning=True),
    'PRECISE': init_llm(provider="ollama", model="gemma4:e2b", thinking_level="high", reasoning=True),
  },
  'gemma4:e4b': {
    'FAST': init_llm(provider="ollama", model="gemma4:e4b", thinking_level="low", reasoning=False),
    'BALANCED': init_llm(provider="ollama", model="gemma4:e4b", thinking_level="medium", reasoning=True),
    'PRECISE': init_llm(provider="ollama", model="gemma4:e4b", thinking_level="high", reasoning=True),
  },
  # 'google/gemma-4-E4B-it': {
  #   'FAST': init_llm(provider="openai", model="google/gemma-4-E4B-it", thinking_level="low", reasoning=False),
  #   'BALANCED': init_llm(provider="openai", model="google/gemma-4-E4B-it", thinking_level="medium", reasoning=True),
  #   'PRECISE': init_llm(provider="openai", model="google/gemma-4-E4B-it", thinking_level="high", reasoning=True),
  # },
}
