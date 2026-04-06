from langchain.messages import HumanMessage, SystemMessage
from utils.logger import getLogger
from ..state import LLM, State, soul

_logger = getLogger(__name__)

SYS_PROMPT = """
Provide material estimate based on the provided context.
When providing the answer, include the citations corresponding to the sources in the context. 
Only include sources that are relevant to the answer.
If the context does not contain relevant information, provide a concise answer based on your knowledge without citing any sources. 
Keep the answer under 150 words. Do not add other information or commentary. Just provide the direct answer with citations if applicable.
Do not use Markdown syntax.

### Sample Response:
Material: the material name
Price: the amount per unit
Unit: the unit used for pricing e.g. 40kg
Source: web url or filename with line number

### Context: 
{context}
""".strip()

async def formatted_response(state: State):
  """
  Formatted Response
  """
  _logger.info("processing")
  context = "\n\n".join([f"{doc.get('page_content')}\n(source: {doc.get('source', 'Unknown')})" for doc in state["documents"]] if state["documents"] else [])
  color_start='\033[32m'
  color_end='\033[0m'
  _logger.info(f"{color_start}\n{context}{color_end}")

  soul_content = soul()

  messages = [
    SystemMessage(content=soul_content),
    SystemMessage(content=SYS_PROMPT.format(context=context)),
    HumanMessage(content=state["messages"][-1].content)
  ]
  response = await LLM.ainvoke(messages)
  return {"messages": [response]}
