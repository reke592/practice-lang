import fsa from "fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import path from "path";

import * as restaurantPlaceOrderTool from "./tools/retaurant-place-order.js";

export function register(server: McpServer) {
  restaurantPlaceOrderTool.register(server);

  // skill resource
  server.registerResource(
    "restaurant-order-taker",
    "skills://restaurant-order-taker",
    {
      title: "Restaurant Order Taker",
      description:
        "Agent for taking restaurant orders. Inputs should be user requests for food items, quantities, and special instructions. Returns order confirmations and estimated wait times.",
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
