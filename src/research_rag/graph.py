from langgraph.graph import END, START, StateGraph
from research_rag.tools import search_web
from .state import CHECKPOINTER, State
from .nodes import hypothesis, formatted_response, proofread, analyst

def should_search_web(state: State):
    print(f"should_search_web: documents={state['documents']}")
    if not state.get("documents"):
        return "search_web"
    return "formatted_response"

graph_builder = StateGraph(State)
graph_builder.add_node("proofread", proofread)
graph_builder.add_node("hypothesis", hypothesis)
graph_builder.add_node("search_web", search_web)
graph_builder.add_node("formatted_response", formatted_response)
graph_builder.add_node("analyst", analyst)

graph_builder.add_edge(START, "proofread")
graph_builder.add_edge("proofread", "hypothesis")
graph_builder.add_edge("hypothesis", "search_web")
graph_builder.add_edge("search_web", "formatted_response")
graph_builder.add_edge("formatted_response", "analyst")
graph_builder.add_edge("analyst", END)

AGENT = graph_builder.compile(checkpointer=CHECKPOINTER)

AGENT.get_graph().draw_mermaid_png(output_file_path="./research_rag.png")
