---
name: product-prices
description: >-
  Shelf prices from chat vision. prices.json + sightings.jsonl under store/.
  Use when shopping, product cost, or "what did it cost last time".
---

# product-prices

Vision photos with dollar amounts amend `store/prices.json` and append
`store/sightings.jsonl`. Names come from the package above/beside each tag —
price-only stickers still file under the brand on the bag/box, not a guess.
Skip a tag if the package name is unreadable.

Same product again: keep the item, set the new dollar as current, and append a
history row with that photo path + timestamp (and `prev_price` when it changed).
Same photo + same price is a no-op. Agents read via desk live block or:

```bash
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Products/scripts/ProductPrices/product_prices.py" recent
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Products/scripts/ProductPrices/product_prices.py" lookup "sour patch"
```

Do not invent prices — only rows in the store.
