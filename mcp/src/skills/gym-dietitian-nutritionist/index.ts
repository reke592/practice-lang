import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

export function register(server: McpServer) {
  // skill resource
  server.registerResource(
    "gym-dietitian-nutritionist",
    "skills://gym-dietitian-nutritionist",
    {
      title: "Gym Dietitian Nutritionist",
      description: "Expert sports dietitian and nutritionist. Call this tool when users ask for custom meal plans, macro and calorie calculations, supplement advice, or dietary strategies tailored for muscle gain, fat loss, and athletic performance.",
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
