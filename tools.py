"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()

    # Filter by price and size
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and size.lower() not in item["size"].lower():
            continue
        filtered.append(item)

    # Score by keyword overlap with description
    keywords = description.lower().split()
    scored = []
    for item in filtered:
        searchable = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            " ".join(item.get("style_tags", [])),
        ]).lower()
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()
    
    wardrobe_items = wardrobe.get("items", [])
    
    if not wardrobe_items:
        prompt = f"""A user is considering buying this secondhand item:
- Title: {new_item.get('title')}
- Category: {new_item.get('category')}
- Style tags: {', '.join(new_item.get('style_tags', []))}
- Colors: {', '.join(new_item.get('colors', []))}
- Condition: {new_item.get('condition')}

They haven't shared their wardrobe. Give 1-2 suggestions for how this piece is commonly styled — what kinds of items pair well with it, what vibe it suits, and how to wear it."""
    else:
        wardrobe_text = "\n".join(
            f"- {item.get('type', 'item')}: {item.get('color', '')} {item.get('style', '')}"
            for item in wardrobe_items
        )
        prompt = f"""A user is considering buying this secondhand item:
- Title: {new_item.get('title')}
- Category: {new_item.get('category')}
- Style tags: {', '.join(new_item.get('style_tags', []))}
- Colors: {', '.join(new_item.get('colors', []))}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and pieces from their wardrobe. Be specific about which wardrobe pieces to pair it with and why."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    return ""
