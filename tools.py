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
            f"- {item.get('name')} (colors: {', '.join(item.get('colors', []))}; tags: {', '.join(item.get('style_tags', []))})"
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
    if not outfit or not outfit.strip():
        return "Error: outfit description is missing — cannot generate a fit card."
    
    client = _get_groq_client()
    
    prompt = f"""Write a 2-3 sentence Instagram caption for this thrifted outfit.

Item details:
- Title: {new_item.get('title')}
- Price: ${new_item.get('price')}
- Platform: {new_item.get('platform')}

Outfit description:
{outfit}

Rules:
- Write in casual first-person (like a real person posting, not a brand)
- Mention the item name, price, and platform once each, naturally
- Capture the specific vibe of the outfit
- No hashtags, No abnomal formatting.
- Keep it under 3 sentences, you can add emojis if it fits the vibe!"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=1.2,
    )
    return response.choices[0].message.content
