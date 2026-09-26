import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import z from "zod";

export function register(server: McpServer) {
  server.registerTool(
    "restaurant-place-order",
    {
      description: "Places an order for a restaurant item",
      inputSchema: {
        items: z.array(
          z.object({
            item: z.string(),
            quantity: z.number(),
            special_instructions: z.string(),
            unit_price: z.number(),
          }),
        ),
      },
    },
    async ({ items }) => {
      let sum = 0;
      for (const item of items) {
        sum += item.quantity * item.unit_price;
      }
      return {
        content: [
          {
            type: "text",
            text: `Order placed for items: \n${items.map((item) => `- ${item.item} ${item.quantity} x ${item.unit_price}`).join("\n")}\n\nTotal: ${sum}`,
          },
        ],
      };
    },
  );
}
