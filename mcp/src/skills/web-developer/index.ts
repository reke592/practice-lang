import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

import * as calculateSumTool from "./tools/calculate_sum.js";
import * as createFileTool from "./tools/write_file.js";
import * as listFilesTool from "./tools/list_files.js";
import * as readFile from "./tools/read_file.js";
import * as readApiDocs from "./tools/read_api_docs.js";

export function register(server: McpServer) {
  // tools
  calculateSumTool.register(server);
  createFileTool.register(server);
  listFilesTool.register(server);
  readFile.register(server);
  readApiDocs.register(server);

  // skill resource
  server.registerResource(
    "web-developer",
    "skills://web-developer",
    {
      title: "Web Developer",
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
