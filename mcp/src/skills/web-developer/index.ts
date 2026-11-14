import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

import * as calculateSumTool from "./tools/calculate_sum.js";
import * as createFileTool from "./tools/write_file.js";

export function register(server: McpServer) {
  // tools
  calculateSumTool.register(server);
  createFileTool.register(server);

  // skill resource
  server.registerResource(
    "web-developer",
    "skills://web-developer",
    {
      title: "Web Developer Agent",
      description: "Web Developer Task, Programming",
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
