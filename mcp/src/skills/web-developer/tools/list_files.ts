import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import fsa from "fs/promises";
import path from "path";
import z from "zod";
import { tempDir } from "../../../environment.js";

export function register(server: McpServer) {
  // Register a simple tool
  server.registerTool(
    "list_files",
    {
      description: "Use this tool to list all the files in workspace.",
      inputSchema: {
        directory_path: z
          .string()
          .optional()
          .describe("A directory path in workspace"),
      },
    },
    async ({ directory_path }, extra) => {
      const results = await fsa.readdir(
        path.join(tempDir, directory_path || ""),
      );
      return {
        content: [
          {
            type: "text",
            text: `Files in "${directory_path || "."}".\n\n${results.map((v) => `- ${v}`).join("\n")}`,
          },
        ],
      };
    },
  );
}
