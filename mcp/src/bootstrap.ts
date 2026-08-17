import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export async function bootstrap(server: McpServer) {
  await Promise.all([
    // skills
    import("./skills/coding/index.js").then(({ register }) => register(server)),
  ]);
}
