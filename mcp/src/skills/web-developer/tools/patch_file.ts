import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import fs from "fs";
import fsa from "fs/promises";
import path from "path";
import z from "zod";
import { tempDir } from "../../../environment.js";

const header = "<<<SEARCH";
const separator = "=====";
const footer = ">>>REPLACE";
const sample = `
${header}
  hello world
${separator}
  hello new world
${footer}
`;
export function register(server: McpServer) {
  // Register a simple tool
  server.registerTool(
    "patch_file",
    {
      description: "Use this tool to update existing file.",
      inputSchema: {
        filepath: z.string().describe("The filename with extension"),
        old_content: z
          .string()
          .describe("The content to replace in existing file."),
        replacement: z
          .string()
          .describe(`The replacement for the old_content.`),
      },
    },
    async ({ filepath, old_content, replacement }, extra) => {
      const target = path.join(tempDir, filepath);

      const diff_block = `<<<Search\n${old_content}\n=====\n${replacement}\n>>>Replace`;
      console.error(diff_block);

      if (!fs.existsSync(target)) {
        return {
          content: [
            {
              type: "text",
              text: "Error: file not found.",
            },
          ],
        };
      }

      const content = (await fsa.readFile(target)).toString();

      if (!content.includes(old_content)) {
        return {
          content: [
            {
              type: "text",
              text: `Error: Cannot find the old_content to replace in file. Please read the original file and re-run this tool.`,
            },
          ],
        };
      }

      // replace
      await fsa.writeFile(target, content.replace(old_content, replacement));

      return {
        content: [
          {
            type: "text",
            text: `File updated. "${filepath}".\n\n${diff_block}`,
          },
        ],
      };
    },
  );
}
