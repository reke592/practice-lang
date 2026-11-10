import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

export function register(server: McpServer) {
  // skill resource
  server.registerResource(
    "researcher",
    "skills://researcher",
    {
      title: "Researcher",
      description: "Expert researcher for searching relevant documents based on user queries. This researcher uses the similarity search against the documents in the database to find the most relevant documents for the user query.",
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
