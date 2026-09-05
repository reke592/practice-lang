import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

import * as firewallIpAddressTool from "./tools/cyber-security-block-ip-address.js";

export function register(server: McpServer) {
  firewallIpAddressTool.register(server);
  // skill resource
  server.registerResource(
    "cyber-security",
    "skills://cyber-security",
    {
      title: "Cyber Security",
      description:
        "Specialized in analyzing and mitigating cyber threats. Call this tool when users ask for threat intelligence, incident response guidance, or security analysis.",
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
