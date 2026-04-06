import asyncio
from utils.environment import init_environment
from research_rag.tools.dti_rag import update_dti_s3_vectore_store
from research_rag.graph import AGENT

async def main():
  color_green='\033[32m'
  color_end='\033[0m'
  init_environment()
  while True:
    user_input = input("Ask: ")
    if user_input == "/bye":
      break
    elif user_input == "/update":
      await update_dti_s3_vectore_store()
      continue
    state = await AGENT.ainvoke(
      input={
        "messages": [{"role": "user", "content": user_input}],
        "documents": [],
        "citations": [],
        "hypothesis": None
      }, 
      config={
        "configurable": {
          "thread_id": 1
        }
      },
    )

    print(f"{color_green}{state['messages'][-1].content}{color_end}")

if __name__=="__main__":
  asyncio.run(main())
