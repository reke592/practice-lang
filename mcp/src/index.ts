import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { bootstrap } from "./bootstrap.js";

const server = new McpServer({
  name: "MCP Server",
  version: "1.0.0",
});

// Connect using stdio transport
async function main() {
  const transport = new StdioServerTransport();
  await bootstrap(server)
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
