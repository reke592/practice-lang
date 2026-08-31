import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

export function register(server: McpServer) {
  // skill resource
  server.registerResource(
    "gym-physical-therapist",
    "skills://gym-physical-therapist",
    {
      title: "Gym Phisical Therapist",
      description: "Gym physical therapist agent for fitness-related injury management and prevention. Inputs should be user symptoms, current routines, or movement goals. Returns evidence-based advice on rehabilitation protocols, prehabilitation, corrective exercises, safe lifting mechanics, and recovery strategies.",
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
