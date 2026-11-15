import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import fsa from "fs/promises";
import path from "path";
import z from "zod";
import { tempDir } from "../../../environment.js";
import axios from "axios";

export function register(server: McpServer) {
  // Register a simple tool
  server.registerTool(
    "read_api_docs",
    {
      description: "Use this tool to read API documentations.",
      inputSchema: {
        api_documentation_url: z
          .string()
          .describe("The API documentation URL."),
      },
    },
    async ({ api_documentation_url }, extra) => {
      const result = await axios
        .get(api_documentation_url)
        .then((response) => {
          return `Successfully loaded ${api_documentation_url}\n\n${JSON.stringify(response.data)}`;
        })
        .catch((error) => {
          return `Unable to load the url ${api_documentation_url}.\n\n${error}`;
        });

      console.error(result);

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
