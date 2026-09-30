---
name: pantry
description: >-
  Household food stock: what is on the shelf, add/use counts, and which recipes
  that covers. Use when asked about the pantry, groceries on hand, leftovers, or
  what we can cook from stock. Not the nutrition database.
---

# pantry

Shelf counts from `store/stock.json`. If it is not in that file, we do
not have it on file.

```bash
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Products/scripts/Pantry/pantry.py"
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Products/scripts/Pantry/pantry.py" add onion 2 ea
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Products/scripts/Pantry/pantry.py" use onion 1
python3 "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Products/scripts/Pantry/pantry.py" set bananas 6 ea
```

Hidden council tags (not spoken): `<<<PANTRY add onion | 2 | ea>>>`
`<<<PANTRY use onion | 1>>>`.

## Rules

1. Log what they say they bought, used, or still have. Qty can be `some` if they
   did not count.
2. After a cook, offer to `use` the ingredients. Do not auto-drain unless they
   said it was eaten or used up.
3. `cooking` `from-pantry` reads this store. `nutrition` does not change counts.
4. Empty pantry is a valid state. Say so.

Related: `cooking`, `nutrition`, `root-record-registry`.
