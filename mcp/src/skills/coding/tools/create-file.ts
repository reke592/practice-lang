import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import fsa from "fs/promises";
import path from "path";
import z from "zod";
import { tempDir } from "../../../environment.js";

export function register(server: McpServer) {
  // Register a simple tool
  server.registerTool(
    "create-file",
    {
      description: "Use this tool to write new file",
      inputSchema: {
        filepath: z.string().describe("The filename"),
        content: z.string().describe("The file content"),
      },
    },
    async ({ filepath, content }, extra) => {
      await fsa.writeFile(path.join(tempDir, filepath), content);
      return {
        content: [
          {
            type: "text",
            text: `File created "${filepath}".\n\n\`\`\`\n${content}\n\`\`\``,
          },
        ],
      };
    },
  );
}
