import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export async function bootstrap(server: McpServer) {
  await Promise.all([
    // skills
    import("./skills/coding/index.js").then(({ register }) => register(server)),
    import("./skills/gym-dietitian-nutritionist/index.js").then(
      ({ register }) => register(server),
    ),
    import("./skills/gym-physical-therapist/index.js").then(({ register }) =>
      register(server),
    ),
    import("./skills/cyber-security/index.js").then(({ register }) =>
      register(server),
    ),
  ]);
}
