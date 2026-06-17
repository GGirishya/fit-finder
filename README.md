# FitFindr

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Given a natural language query, FitFindr searches mock thrift listings, suggests outfit combinations based on your wardrobe, and generates a shareable caption for the look.

---

## Tool Inventory

### `search_listings(description, size, max_price)`
- **Inputs:** `description` (str) — keywords describing the item; `size` (str or None) — size to filter by, case-insensitive; `max_price` (float or None) — price ceiling in dollars
- **Output:** list of matching listing dicts, each containing `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Returns an empty list if nothing matches.
- **Purpose:** Filters and scores the mock listings dataset by keyword overlap with the description, after applying size and price filters.

### `suggest_outfit(new_item, wardrobe)`
- **Inputs:** `new_item` (dict) — a single listing dict; `wardrobe` (dict) — wardrobe dict with an `items` key containing a list of owned pieces
- **Output:** str — one or more outfit suggestions referencing specific wardrobe pieces, or general styling advice if the wardrobe is empty
- **Purpose:** Calls the Groq LLM to suggest outfit combinations using the new item and the user's existing wardrobe.

### `create_fit_card(outfit, new_item)`
- **Inputs:** `outfit` (str) — the outfit suggestion from `suggest_outfit`; `new_item` (dict) — the listing dict for the thrifted item
- **Output:** str — a 2–3 sentence casual Instagram-style caption mentioning the item name, price, and platform. Returns a descriptive error string if `outfit` is empty.
- **Purpose:** Generates a shareable, varied caption that captures the vibe of the outfit in first-person voice.

---

## How the Planning Loop Works

`run_agent()` in `agent.py` runs the following conditional logic:

1. Parse the user's query using regex to extract a description, size (e.g. "size M"), and max price (e.g. "under $30"). Store in `session["parsed"]`.
2. Call `search_listings()` with the parsed parameters. Store results in `session["search_results"]`.
3. **Branch:** if results is empty, set `session["error"]` to a helpful message and return the session immediately — `suggest_outfit` and `create_fit_card` are never called.
4. If results exist, set `session["selected_item"]` to the top result.
5. Call `suggest_outfit()` with the selected item and wardrobe. Store the result in `session["outfit_suggestion"]`.
6. Call `create_fit_card()` with the outfit suggestion and selected item. Store the result in `session["fit_card"]`.
7. Return the session.

The agent does not call all three tools unconditionally — step 3 is a real branch that changes behavior based on what `search_listings` returns.

---

## State Management

A single `session` dict is initialized at the start of `run_agent()` and passed through each step:

```python
session = {
    "query": query,
    "parsed": {},
    "search_results": [],
    "selected_item": None,
    "wardrobe": wardrobe,
    "outfit_suggestion": None,
    "fit_card": None,
    "error": None,
}
```

Each tool writes its output into the session before the next tool reads from it. `suggest_outfit` receives `session["selected_item"]` — the exact dict returned by `search_listings`. `create_fit_card` receives `session["outfit_suggestion"]` and `session["selected_item"]`. No tool re-prompts the user or uses hardcoded values between steps.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query | Sets `session["error"]` = "No listings matched your search. Try broadening your description, removing the size filter, or raising your max price." Returns session early — outfit and fit card are never called. |
| `suggest_outfit` | Wardrobe is empty | Detects `wardrobe["items"] == []` and switches to a different LLM prompt asking for general styling advice instead of wardrobe-specific combinations. Returns a non-empty string — never crashes. |
| `create_fit_card` | `outfit` is an empty string | Returns `"Error: outfit description is missing — cannot generate a fit card."` without calling the LLM. |

**Concrete example from testing:**

Running `python agent.py` with query `"designer ballgown size XXS under $5"` produced:

```
error: No listings matched your search. Try broadening your description, removing the size filter, or raising your max price.
fit_card: None
```

The agent stopped after `search_listings` returned `[]` and never called the remaining two tools.

---

## Spec Reflection

**One way the spec helped:** Designing the planning loop in `planning.md` before writing any code made the conditional branching in `run_agent()` straightforward to implement. Having the exact session dict fields defined in advance meant there was no ambiguity about what to store or when.

**One way implementation diverged:** The spec assumed `suggest_outfit` would receive a wardrobe with `type`, `color`, and `style` fields per item. The actual `wardrobe_schema.json` uses `name`, `colors` (a list), and `style_tags` (a list) instead. The prompt formatting had to be updated to use `item.get("name")` and join the list fields — the spec didn't catch this because it was written before inspecting the actual schema closely enough.

---

## AI Usage

**Instance 1 — `search_listings` implementation:**
I gave Claude the Tool 1 spec from `planning.md` (inputs, return value, failure mode) and asked it to implement the function using `load_listings()` from the data loader. The generated code was correct but I verified it handled `None` size and price gracefully before running it. I tested it with three queries — a broad match, a price-filtered match, and a deliberate no-results case, before trusting it.

**Instance 2 — planning loop implementation:**
I gave Claude the full agent diagram and the Planning Loop and State Management sections from `planning.md` and asked it to implement `run_agent()`. The generated code matched the spec's conditional logic. I reviewed it before running to confirm it branched on `results == []`, stored values in the session dict rather than local variables, and did not call all three tools unconditionally. I then tested the no-results branch explicitly with `python agent.py`.
