import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import fs from "fs";
import fsa from "fs/promises";
import path from "path";
import z from "zod";
import { tempDir } from "../../../environment.js";

export function register(server: McpServer) {
  // Register a simple tool
  server.registerTool(
    "read_file",
    {
      description: "Use this tool to read a file in workspace.",
      inputSchema: {
        file_path: z.string().describe("A directory path in workspace"),
      },
    },
    async ({ file_path }, extra) => {
      const target = path.resolve(path.join(tempDir), file_path);
      let result = `${file_path} Not Found.`;
      if (fs.existsSync(target)) {
        result = (await fsa.readFile(target)).toString();
      }
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    },
  );
}
