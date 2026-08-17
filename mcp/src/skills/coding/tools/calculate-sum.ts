import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import z from "zod";

export function register(server: McpServer) {
  // Register a simple tool
  server.registerTool(
    "calculate-sum",
    {
      description: "Adds two numbers together",
      inputSchema: {
        a: z.number().describe("First number"),
        b: z.number().describe("Second number"),
      },
    },
    async ({ a, b }) => {
      return {
        content: [
          {
            type: "text",
            text: `The sum is ${a + b}`,
          },
        ],
      };
    },
  );
}
