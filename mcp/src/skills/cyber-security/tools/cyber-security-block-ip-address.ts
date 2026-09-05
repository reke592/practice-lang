import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import z from "zod";

export function register(server: McpServer) {
  server.registerTool(
    "cyber-security-block-ip-address",
    {
      description: "Blocks a specific IP address",
      inputSchema: {
        ipAddress: z.string().describe("The IP address to block"),
      },
    },
    async ({ ipAddress }) => {
      return {
        content: [
          {
            type: "text",
            text: `IP address blocked: ${ipAddress}`,
          },
        ],
      };
    },
  );
}
