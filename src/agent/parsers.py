import copy

from langchain_core.messages import AIMessage

from constants import COLOR_GREEN, COLOR_GREY, COLOR_RESET


def ToolAwareParser(message: AIMessage) -> AIMessage:
  if hasattr(message, 'usage_metadata') and message.usage_metadata:
    print(f"{COLOR_GREY}{message.usage_metadata}{COLOR_RESET}")
  
  print(f"{COLOR_GREEN}{message}{COLOR_RESET}")
  if hasattr(message,'tool_calls') and len(message.tool_calls) > 0:
    return message
  
  if hasattr(message, 'text') and message.text:
    msg = copy.copy(message)
    msg.content = message.text
    if isinstance(getattr(msg, 'content', None), list):
      msg = copy.copy(message)
      msg.content = " ".join([part['text'] for part in message.content if isinstance(part, dict) and 'text' in part])
    return msg

  if isinstance(getattr(message, 'content', None), list):
    msg = copy.copy(message)
    msg.content = " ".join([part['text'] for part in message.content if isinstance(part, dict) and 'text' in part])
    return msg
  
  return message