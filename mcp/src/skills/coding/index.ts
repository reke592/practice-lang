import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import * as calculateSumTool from "./tools/calculate-sum.js";
import path from "path";

export function register(server: McpServer) {
  // tools
  calculateSumTool.register(server);

  // skill resource
  server.registerResource(
    "coding",
    "skills://coding",
    {
      title: "Coding Agent",
      description: "Coding Task, Programming",
      mimeType: "text/plain",
    },
    async (uri, extra) => {
      const data = await fsa.readFile(
        path.join(import.meta.dirname, "SKILL.md"),
      );
      return {
        contents: [
          {
            uri: uri.href,
            text: data.toString(),
          },
        ],
      };
    },
  );
}
