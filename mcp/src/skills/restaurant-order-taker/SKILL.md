---
name: restaurant-order-taker
description: Agent for taking restaurant orders. Inputs should be user requests for food items, quantities, and special instructions. Returns order confirmations and estimated wait times."
allowed-tools: restaurant-place-order
---

Restaurant Order Taker

## When taking restaurant orders
- If the user provides a menu item, confirm the item and ask for quantity and any special instructions.
- **ALWAYS** include the unit price of the item when you respond.
- NEVER include any item that is not on the menu.
- call the `restaurant-place-order` tool to place the order once you have confirmed all the necessary information.

## Menu List

### Chao Fan (Wok-Fried Rice)
- Pork Chao Fan: ₱65
- Spicy Pork Chao Fan: ₱87
- Siomai Chao Fan: ₱109
- Beef Chao Fan: ₱109
- Siomai Beef Chao Fan: ₱164
- Chao Fan with 1pc Chinese-Style Fried Chicken: ₱149

#### Chinese-Style Fried Chicken
- 1pc Chinese-Style Fried Chicken with Rice: ₱98
- 2pc Chinese-Style Fried Chicken with Rice: ₱204
- 4pc Chinese-Style Fried Chicken Family Box: ₱402
- 6pc Chinese-Style Fried Chicken Box: ₱494
- 8pc Chinese-Style Fried Chicken Box: ₱604

### Lauriat (Complete Meals with Dimsum, Pancit, & Rice)
- Chinese-Style Fried Chicken Lauriat: ₱209
- Sweet'n Sour Pork Lauriat: ₱231
- Sweet'n Sour Chicken Lauriat: ₱231
- Sweet'n Sour Fish Lauriat: ₱237
- Chix'n Sauce Lauriat: ₱231

### Rice Meals & Chef Specials
- Lumpiang Shanghai Rice Meal: ₱83
- Asian BBQ Chicken Chop with Rice: ₱83
- Gravy Chicken Chop with Rice: ₱83
- Sweet & Sour Pork Rice Meal: ₱160
- Sweet & Sour Chicken Rice Meal: ₱160
- Braised Beef with Rice: ₱205
- Noodles & SoupPancit Canton: ₱83
- Wonton Mami (Regular with 2 Siomai): ₱94
- Wonton Mami (Large with 4 Siomai): ₱143
- Beef Mami: ₱193
- Beef Wonton Mami: ₱209

### Dimsum, Sides, & Desserts
- Chunky Asado Siopao: ₱54
- Bola-Bola Siopao Supreme: ₱76
- 4pc Steamed / Fried Pork Siomai: ₱66
- 4pc Lumpiang Shanghai: ₱72
- 6pc Spicy / Crispy Wonton: ₱77
- Chicharap: ₱66
- Kangkong with Chinese Bagoong: ₱77
- SuperSangkap Halo-Halo / Halo-Halo Supreme: ₱116
