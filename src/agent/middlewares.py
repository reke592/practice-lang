import asyncio
import traceback
from langchain_core.tools import BaseTool
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from constants import COLOR_MAGENTA, COLOR_RESET

async def tool_call_middleware(request: ToolCallRequest, execute) -> ToolMessage | Command:
    """Middleware that intercepts tool executions and extracts custom resource metadata"""
    try:
        # 1. Execute the tool via ToolNode
        result: ToolMessage | Command = await execute(request)
        
        if isinstance(result, Command):
           return result

        # Safe checking for tool error conventions
        if isinstance(result.content, list) and len(result.content) > 0:
            first_item = result.content[0]
            if isinstance(first_item, dict) and first_item.get('text', '').startswith("ToolCallError"):
                print(f"{COLOR_MAGENTA}{result}{COLOR_RESET}")
                raise Exception(first_item['text'].replace("ToolCallError", "").strip())


        if isinstance(result.content, str):
            # 2. Extract multi-content payload from the MCP result
            # (Assuming you updated your TS server to return Option 2 text blocks or option 1 JSON)
            extracted_artifact = {}
            cleaned_content_list = []
            # If LangChain already flattened it to a single string, parse via lines
            lines = result.content.split('\n')
            for line in lines:
                if "RESOURCE_LINK:" in line:
                    extracted_artifact["resource"] = line.replace("RESOURCE_LINK:", "").strip()
                else:
                    cleaned_content_list.append(line)
            
            # Reconstruct content without exposing raw protocol link variables directly to the LLM
            if "resource" in extracted_artifact:
                result.content = "\n".join(cleaned_content_list).strip()
                result.artifact = extracted_artifact

        elif isinstance(result.content, list):
            # If it comes back as a raw list of contents from the MCP client
            final_text_blocks = []
            extracted_artifacts = []
            for item in result.content:
                extracted_artifact = {}
                if isinstance(item, dict):
                    # Catch the custom text block variant
                    text_val = item.get("text", "")
                    if "RESOURCE_LINK:" in text_val:
                        extracted_artifacts.append({
                           'resource': text_val.replace("RESOURCE_LINK:", "").strip()
                        })
                    else:
                        final_text_blocks.append(text_val)
                    
                    # Catch the compliant 'resource' variant (Option 1 from prior step)
                    if item.get("type") == "resource" and "resource" in item:
                        # extracted_artifact["resource"] = item["resource"].get("uri")
                        extracted_artifacts.append({
                           'resource': item["resource"].get("uri")
                        })

            # Update the message properties
            result.content = "\n".join(final_text_blocks).strip()
            if extracted_artifacts:
                result.artifact = extracted_artifacts

        return result
    
    # --- CRITICAL HITL EXCEPTION HANDLING ---
    except GraphInterrupt:
        # 1. Bubble up LangGraph's intentional interrupts to pause the graph for the human.
        raise

    except asyncio.CancelledError:
        # 2. Prevent async task cancellations from being swallowed and reported as tool errors.
        raise
    
    except Exception as e:
        print(f"Intercepted exception in tool '{request.tool_call['name']}': {e}")
        traceback.print_exc()
        return ToolMessage(
            content=str(e),
            tool_call_id=request.tool_call['id'],
            name=request.tool_call["name"],
            status="error"
        )