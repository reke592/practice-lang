from mcp import ClientSession

from agent.schemas import MCPSkill


async def load_mcp_skills(session: ClientSession, scheme: str | None = "skills") -> tuple[list[MCPSkill], str]:
  """Load the skills from the MCP session"""
  result = await session.list_resources()

  mcp_skills: list[MCPSkill] = []
  descriptions: list[str] = [
    "| Name | Description |",
    "|------|-------------|"
  ]

  # print(result.resources)

  for item in result.resources:
    if not item.uri.scheme == scheme:
      continue
    mcp_skills.append(MCPSkill.model_validate({
      'name': item.name,
      'description': item.description,
      'uri': f"{item.uri}"
    }))
    descriptions.append(f"| {item.name} | {item.description} |")

  return mcp_skills, "\n".join(descriptions)