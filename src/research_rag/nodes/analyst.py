from langchain.messages import HumanMessage, SystemMessage
from utils.logger import getLogger
from ..state import LLM, State, soul

_logger = getLogger(__name__)

SYS_PROMPT = """
You are a Senior Construction Cost Analyst. Your task is to analyze the raw price data 
provided and synthesize a single "Recommended Market Price" for each material.

### Analysis Rules:
1. **Filter Outliers:** Ignore prices that are obviously incorrect (e.g., ₱0.00) or 
   extreme outliers (e.g., prices 50% above or below the median) unless justified.
2. **Prioritize Recency & Location:** Favor sources that are more recent or specific 
   to the project's region (Philippines/Bulacan).
3. **Determine the Range:** Provide the Low, High, and a "Recommended" price.
4. **Logic Check:** If a price seems too low (like ₱149 for a 6m Rebar in 2026), 
   flag it as "Likely Retail/Substandard" or "Incomplete Data."

### Final Output Format:
# MATERIAL ANALYSIS: [Material Name]

**Market Summary:**
- **Lowest Valid Price:** ₱[Amount] ([Source])
- **Highest Valid Price:** ₱[Amount] ([Source])
- **Recommended Estimate:** ₱[Amount] per [Unit]

**Analyst Notes:**
- [Briefly explain why you picked the recommended price]
- [Note any suspicious data points filtered out]
""".strip()

async def analyst(state: State):
  """
  Formatted Response
  """
  _logger.info("processing")

  soul_content = soul()
  
  messages = [
    SystemMessage(content=soul_content),
    SystemMessage(content=SYS_PROMPT),
    HumanMessage(content=f"Analyze these raw results:\n{state['messages'][-1].content}")
  ]
  response = await LLM.ainvoke(messages)
  return {"messages": [response]}
