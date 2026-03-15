from langchain_core.messages import BaseMessage
from utils.logger import getLogger
from typing import Sequence

logger = getLogger(__name__)

def history_as_turns(chat_history: Sequence[BaseMessage]) -> list[Sequence[BaseMessage]]:
  logger.info("history_as_turns..")
  if not len(chat_history):
    return []
  
  turns = []
  for i in range(len(chat_history)):
    message = chat_history[i]
    if message.type in ["human","user"]:
      turns.append([message])
    elif message.type in ["ai", "assistant"]:
      if turns:
        turns[-1].append(message)
      else:
        turns.append([message])
  return turns


def formatted_turns(turns: list[Sequence[BaseMessage]]) -> list:
  logger.info("formatted_turns..")
  chat_messages = []
  for i, turn in enumerate(turns):
    formatted = []
    for message in turn:
      content = message.content.replace('\n', '\\n') if message.content is str else message.content
      formatted.append(f"{message.type.upper()}: {content}")
    chat_messages.append(f"Turn {i + 1}:\n" + "\n".join(formatted))
  return chat_messages
