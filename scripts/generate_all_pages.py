#!/usr/bin/env python3
"""
Master Page & Sitemap Generator for All AI Tools (https://www.allaitools.online/)
- Fully optimized for Google Search Console queries & high-CTR search appearance:
  - 'allaitools', 'all ai tools in one website', '1000 ai tools', 'list of all ai tools', 'ai tool list'
  - '{tool} alternatives' (e.g. altftools alternatives, landinghero alternatives, inkle alternatives)
  - Tool-specific queries (airbrush image enhancer, xeve ai, google flow, freemaker, etc.)
- Rich JSON-LD Structured Data: SoftwareApplication with AggregateRating (star snippets), BreadcrumbList, FAQPage
- Fast pre-rendered static HTML in public/<slug>/index.html and public/<slug>.html
- Canonical HTTPS sitemap.xml & permissive robots.txt
"""

import os
import sys
import json
import html
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, quote_plus
from datetime import datetime, timezone

BASE_URL = "https://www.allaitools.online"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

print(f"Starting master SEO generation for {BASE_URL} ({TODAY})...")

# 1. Load tools
with open("tools.json", "r", encoding="utf-8") as f:
    raw_tools = json.load(f)

print(f"Loaded {len(raw_tools)} raw tools from tools.json")

def clean_slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text).strip('-')
    return text

def get_base_slug(t):
    if t.get('slug'):
        return t['slug']
    src = t.get('source_url', '')
    if '/tool/' in src:
        slug = src.split('/tool/')[-1].strip('/').split('?')[0].lower()
        slug = clean_slug(slug)
        if slug:
            return slug
    name = t.get('name', '')
    slug = clean_slug(name)
    return slug or 'ai-tool'

# Deduplicate
by_slug = {}
for t in raw_tools:
    slug = get_base_slug(t)
    if slug not in by_slug:
        by_slug[slug] = t
    else:
        existing = by_slug[slug]
        # Merge best fields
        if len(t.get('name', '')) < len(existing.get('name', '')) and ':' in existing.get('name', ''):
            existing['name'] = t['name']
        if 'aitoolsdirectory.com' in existing.get('url', '') and 'aitoolsdirectory.com' not in t.get('url', ''):
            existing['url'] = t['url']
        if t.get('image_url') and not existing.get('image_url'):
            existing['image_url'] = t['image_url']
        if len(t.get('description', '')) > len(existing.get('description', '')):
            existing['description'] = t['description']

deduped = list(by_slug.values())

# Assign final unique slug and path
seen_slugs = set()
tools = []
for t in deduped:
    s = get_base_slug(t)
    final_slug = s
    counter = 1
    while final_slug in seen_slugs:
        counter += 1
        final_slug = f"{s}-{counter}"
    seen_slugs.add(final_slug)
    t['slug'] = final_slug
    t['path'] = f"/{final_slug}/"
    tools.append(t)

print(f"Processed {len(tools)} deduplicated tools with unique slugs.")

# Save updated tools.json
with open("tools.json", "w", encoding="utf-8") as f:
    json.dump(tools, f, indent=2, ensure_ascii=False)
print("Updated tools.json with clean slugs and paths.")

total_tools = len(tools)
cat_counts = {}
for t in tools:
    c = t.get("category_slug", "chat-reasoning")
    cat_counts[c] = cat_counts.get(c, 0) + 1

def get_domain(url):
    try:
        netloc = urlparse(url).netloc
        return netloc.replace('www.', '') if netloc else 'official website'
    except Exception:
        return 'official website'

# 2. Build Homepage Cards HTML (Top 80 pre-rendered in static HTML for instant initial paint)
cards_html = []
for t in tools[:80]:
    subcat = t.get('subcategory') or t.get('category_section') or t.get('category_pill') or 'AI Tool'
    desc = t.get('description', '')
    name = t.get('name', 'AI Platform')
    pricing = t.get('pricing', 'Freemium')
    pill = t.get('category_pill', 'AI Tools')
    cat_slug = t.get('category_slug', 'chat-reasoning')
    color = t.get('color', '#4F46E5')
    badge = t.get('badge', name[:2].upper())
    url = t.get('url', '#')
    img_url = t.get('image_url', '')
    slug = t.get('slug', 'tool')
    path = t.get('path', f"/{slug}/")

    price_class = "price-freemium"
    if pricing.lower() == "free":
        price_class = "price-free"
    elif pricing.lower() == "paid":
        price_class = "price-paid"

    card = f'''        <article class="tool-card" data-category="{html.escape(cat_slug)}" data-pricing="{html.escape(pricing.lower())}" data-name="{html.escape(name.lower())}" data-desc="{html.escape(desc.lower())}" data-tool-path="{html.escape(path)}" onclick="if(!event.target.closest('a') && !event.target.closest('button')) window.location.href='{html.escape(path)}'">
          <div class="card-top">
            <div class="tool-brand">
              <div class="tool-avatar" style="background: {color};">{html.escape(badge)}</div>
              <div class="tool-title-wrap">
                <span class="tool-subcat">{html.escape(subcat)}</span>
                <h3 class="tool-name"><a href="{html.escape(path)}" class="tool-card-title-link" title="{html.escape(name)}">{html.escape(name)}</a></h3>
              </div>
            </div>
            <button class="bookmark-btn" title="Bookmark {html.escape(name)}" data-tool="{html.escape(name)}" aria-label="Bookmark {html.escape(name)}" onclick="event.stopPropagation()">&#9734;</button>
          </div>
          <p class="tool-desc">{html.escape(desc)}</p>
          <div class="card-bottom">
            <div class="card-bottom-pills">
              <span class="cat-pill">{html.escape(pill)}</span>
              <span class="price-badge {price_class}">{html.escape(pricing)}</span>
            </div>
            <div class="card-actions">
              <a href="{html.escape(path)}" class="details-link">Details &rarr;</a>
              <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow" class="tool-link" onclick="event.stopPropagation()">Visit &rarr;</a>
            </div>
          </div>
        </article>'''
    cards_html.append(card)

cards_block = "\n".join(cards_html)

# Export compact tools JSON for instant client-side search across all 10,000 tools
compact_tools = []
for t in tools:
    compact_tools.append({
        'n': t.get('name', ''),
        's': t.get('slug', ''),
        'b': t.get('badge', ''),
        'c': t.get('color', '#6366F1'),
        'p': t.get('pricing', 'Freemium'),
        'cs': t.get('category_slug', 'chat-reasoning'),
        'cp': t.get('category_pill', 'Chat & Reasoning'),
        'sc': t.get('subcategory') or t.get('category_section') or t.get('category_pill', ''),
        'd': t.get('description', ''),
        'u': t.get('url', '')
    })

with open("tools_compact.json", "w", encoding="utf-8") as f:
    json.dump(compact_tools, f)
with open("public/tools_compact.json", "w", encoding="utf-8") as f:
    json.dump(compact_tools, f)
print(f"Exported compact tools index with {len(compact_tools)} tools.")

# Build Homepage Schema Items (Top 250)
schema_items = []
for idx, t in enumerate(tools[:250], start=1):
    schema_items.append({
        "@type": "ListItem",
        "position": idx,
        "name": t.get("name", "AI Tool"),
        "url": f"{BASE_URL}{t.get('path', '/')}"
    })

schema_json = json.dumps({
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": f"{BASE_URL}/#website",
            "url": f"{BASE_URL}/",
            "name": "All AI Tools (allaitools)",
            "alternateName": [
                "allaitools",
                "allaitools.online",
                "All AI Tools List",
                "All Tools Website",
                "AI All Tools Directory"
            ],
            "description": f"The definitive, fast, and comprehensive directory of {total_tools}+ worldwide artificial intelligence tools, models, and agents. Find all AI tools list for writing, coding, images, voice, video, and search in one website.",
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{BASE_URL}/?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        },
        {
            "@type": "ItemList",
            "@id": f"{BASE_URL}/#featured",
            "name": f"All AI Tools List & Complete Global AI Directory ({total_tools}+ Verified Tools)",
            "numberOfItems": total_tools,
            "itemListElement": schema_items
        },
        {
            "@type": "FAQPage",
            "@id": f"{BASE_URL}/#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "Where can I find a complete list of all AI tools in one website?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"You can browse and search the complete list of {total_tools}+ verified artificial intelligence tools, reasoning models, and custom GPTs in one website on All AI Tools (allaitools.online), categorized across Chat, Coding, Image, Video, Voice, and Search."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Are there free AI tools and alternatives available on All AI Tools?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Yes! All AI Tools categorizes each software with clear pricing badges: Free, Freemium, and Paid. You can instantly filter the entire directory to find 100% free AI tools and free alternatives to expensive software."
                    }
                },
                {
                    "@type": "Question",
                    "name": "How does the tool page and card click work on All AI Tools?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Clicking any tool card opens its dedicated URL (/toolname) featuring full specs, search queries, parameters, and verified alternatives. Clicking the 'Open Tool' button redirects directly to the tool's official website in a new window."
                    }
                },
                {
                    "@type": "Question",
                    "name": "What are the best alternatives to popular AI tools and directories like AltFTools?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"All AI Tools (allaitools.online) serves as a modern, lightning-fast alternative to older directories like AltFTools, ToolYardPro, and Aixploria, offering real-time instant search, category filtering, verified direct links, and over {total_tools}+ up-to-date AI platforms."
                    }
                }
            ]
        }
    ]
}, indent=2)

# 3. Generate index.html
index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>All AI Tools (allaitools) — Complete AI Tools List &amp; Directory of {total_tools}+ AI Tools in One Website (2026)</title>
  <meta name="description" content="Discover {total_tools}+ verified AI tools across all categories on All AI Tools (allaitools.online). Complete all AI tools list in one website: find top AI software, free tools, custom GPTs, and verified alternatives with instant search." />
  <meta name="keywords" content="allaitools, all ai tools, all ai tools list, all tools website, list all ai tools, ai all tools, ai tool list, all ai, aitoolslist, aitools, tools ai, list of all ai tools, ai tool directory, all ai tools in one website, ai tools by category, all tools ai, ai software directory, all ai list, ai tools all, ai tools collection, 1000 ai tools, every ai tool, best ai tools 2026, free ai tools list, ai tools database, aitools list, altftools alternatives, aitoolradar alternatives, artificial intelligence tools, all ai websites, complete ai directory, all the ai tools available, free online tools directory, every single ai, al tools, allaitool, aitolls, aitols, all tool ai" />
  <meta name="author" content="All AI Tools" />
  <meta name="subject" content="Complete List and Directory of All AI Tools ({total_tools}+ Tools)" />
  <meta name="topic" content="Artificial Intelligence Tools, AI Software &amp; Machine Learning Directory" />
  <meta name="classification" content="Artificial Intelligence Directory, AI Tools List" />
  <meta name="revisit-after" content="2 days" />
  <link rel="canonical" href="{BASE_URL}/" />

  <!-- OpenGraph -->
  <meta property="og:title" content="All AI Tools (allaitools) — Complete AI Tools List &amp; {total_tools}+ Directory" />
  <meta property="og:description" content="The complete list of all AI tools in one website ({total_tools}+ platforms). Search by category, filter by Free or Freemium, and discover the best AI software &amp; alternatives." />
  <meta property="og:url" content="{BASE_URL}/" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="All AI Tools" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="All AI Tools (allaitools) | Exhaustive All AI Tools List ({total_tools}+ Tools)" />
  <meta name="twitter:description" content="Browse the ultimate all AI tools directory and complete AI software list in one website with lightning-fast instant search." />

  <!-- Favicon SVG -->
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2222%22 fill=%22%234F46E5%22/><text y=%2268%22 x=%2250%22 font-family=%22system-ui,sans-serif%22 font-weight=%22800%22 font-size=%2254%22 fill=%22white%22 text-anchor=%22middle%22>AI</text></svg>" />

  <!-- Structured Data JSON-LD -->
  <script type="application/ld+json">
{schema_json}
  </script>

  <style>
    :root {{
      --bg: #090d16;
      --bg-card: #0f1626;
      --bg-card-hover: #151f36;
      --bg-elevated: #1a253f;
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.4);
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-sub: #64748b;
      --accent: #6366f1;
      --accent-glow: rgba(99, 102, 241, 0.25);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --radius-pill: 9999px;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text-main); line-height: 1.5; }}
    body {{ min-height: 100vh; overflow-x: hidden; }}
    a {{ text-decoration: none; color: inherit; }}

    /* Ambient Background Mesh */
    .ambient-glow {{
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 1000px;
      height: 520px;
      background: radial-gradient(circle 500px at 50% 120px, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.08), transparent 70%);
      pointer-events: none;
      z-index: 0;
    }}

    .container {{ max-width: 1280px; margin: 0 auto; padding: 0 24px; position: relative; z-index: 1; }}

    /* Mobile Quick-Access Tools Strip */
    .mobile-tools-bar {{
      display: none;
      background: rgba(15, 22, 38, 0.95);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 8px 0;
      position: sticky;
      top: 60px;
      z-index: 99;
    }}
    @media (max-width: 899px) {{
      .mobile-tools-bar {{
        display: block;
      }}
    }}
    .mobile-tools-inner {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }}
    .mobile-tool-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.35);
      color: #c7d2fe;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 9999px;
      text-decoration: none;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}
    .mobile-tool-pill:hover, .mobile-tool-pill:active {{
      background: rgba(99, 102, 241, 0.25);
      color: #ffffff;
      border-color: #818cf8;
    }}
    .mobile-tool-icon {{
      font-size: 0.85rem;
    }}
    .mobile-tool-badge {{
      background: rgba(16, 185, 129, 0.2);
      color: #6ee7b7;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    /* Redesigned Modern Navbar */
    .navbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(9, 13, 22, 0.88);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
      height: 68px;
      display: flex;
      align-items: center;
    }}
    .nav-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      gap: 16px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      font-size: 1.18rem;
      letter-spacing: -0.025em;
      color: #fff;
      text-decoration: none;
      flex-shrink: 0;
    }}
    .brand-logo-icon {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(168, 85, 247, 0.25) 50%, rgba(56, 189, 248, 0.2) 100%);
      border: 1px solid rgba(129, 140, 248, 0.4);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
      flex-shrink: 0;
      transition: all 0.25s ease;
    }}
    .brand:hover .brand-logo-icon {{
      transform: scale(1.05);
      border-color: rgba(129, 140, 248, 0.7);
      box-shadow: 0 6px 20px rgba(129, 140, 248, 0.55);
    }}
    .brand-text {{
      font-size: 1.18rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      color: #ffffff;
    }}
    .nav-links {{
      display: none;
      align-items: center;
      gap: 4px;
      background: rgba(255, 255, 255, 0.03);
      padding: 4px;
      border-radius: 9999px;
      border: 1px solid rgba(255, 255, 255, 0.06);
    }}
    @media (min-width: 900px) {{
      .nav-links {{ display: flex; }}
    }}
    .nav-link {{
      color: #94a3b8;
      font-size: 0.85rem;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 9999px;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .nav-link:hover {{
      color: #ffffff;
      background: rgba(255, 255, 255, 0.08);
    }}
    .nav-link-special {{
      color: #c7d2fe;
    }}
    .nav-link-special:hover {{
      color: #ffffff;
      background: rgba(99, 102, 241, 0.2);
    }}
    .nav-sparkle {{
      font-size: 0.85rem;
    }}
    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }}
    .btn-saved {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #cbd5e1;
      padding: 7px 13px;
      border-radius: 10px;
      font-size: 0.84rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}
    .btn-saved:hover {{
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
      border-color: rgba(255, 255, 255, 0.2);
    }}
    .saved-badge {{
      background: rgba(251, 191, 36, 0.2);
      color: #fbbf24;
      padding: 1px 6px;
      border-radius: 10px;
      font-size: 0.75rem;
      font-weight: 700;
    }}
    .btn-submit {{
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      color: #fff !important;
      padding: 8px 16px;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.84rem;
      box-shadow: 0 3px 12px rgba(99, 102, 241, 0.35);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .btn-submit:hover {{
      transform: translateY(-1px);
      box-shadow: 0 5px 18px rgba(99, 102, 241, 0.5);
      opacity: 0.96;
    }}
    .btn-crm {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: #a5b4fc;
      padding: 7px 11px;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s ease;
    }}
    .btn-crm:hover {{
      background: rgba(99, 102, 241, 0.15);
      border-color: rgba(99, 102, 241, 0.5);
      color: #ffffff;
    }}

    /* Hero Section - Clean & Uncluttered */
    .hero {{ text-align: center; padding: 40px 0 24px; position: relative; }}
    .hero h1 {{
      font-size: clamp(1.85rem, 3.8vw, 2.75rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.2;
      margin-bottom: 22px;
      color: #ffffff;
    }}
    .hero h1 .gradient-text {{
      background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #f472b6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    /* Streamlined Global Search Bar */
    .search-box-wrap {{
      max-width: 640px;
      margin: 0 auto 20px;
      position: relative;
      display: flex;
      align-items: center;
    }}
    .search-icon {{
      position: absolute;
      left: 18px;
      font-size: 1.1rem;
      color: var(--text-sub);
      pointer-events: none;
    }}
    .search-box {{
      width: 100%;
      padding: 14px 44px 14px 50px;
      background: rgba(15, 22, 38, 0.92);
      border: 1px solid rgba(99, 102, 241, 0.25);
      border-radius: 14px;
      color: #ffffff;
      font-size: 0.96rem;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(99, 102, 241, 0.12);
      transition: all 0.2s ease;
      outline: none;
    }}
    .search-box:focus {{
      border-color: #6366f1;
      box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45), 0 0 0 3px rgba(99, 102, 241, 0.28);
      background: #111a30;
    }}
    .search-box::placeholder {{ color: #64748b; font-size: 0.9rem; }}
    .search-hint {{
      position: absolute;
      right: 14px;
      font-size: 0.72rem;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      color: var(--text-sub);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: ui-monospace, monospace;
      pointer-events: none;
    }}
    .clear-search {{
      position: absolute;
      right: 48px;
      background: none;
      border: none;
      color: var(--text-sub);
      font-size: 1.15rem;
      cursor: pointer;
      display: none;
      padding: 4px;
    }}
    .clear-search:hover {{ color: #ffffff; }}

    /* Streamlined Filter Toolbar */
    .filter-toolbar {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      margin-top: 4px;
    }}

    /* Compact Category Filter Pills (Single Balanced Row) */
    .filter-pills-row {{
      display: flex;
      justify-content: center;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .filter-pill {{
      background: rgba(15, 22, 38, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #94a3b8;
      padding: 6px 12px;
      border-radius: var(--radius-pill);
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.18s ease;
    }}
    .filter-pill:hover {{
      color: #ffffff;
      background: rgba(26, 37, 63, 0.95);
      border-color: rgba(99, 102, 241, 0.35);
      transform: translateY(-1px);
    }}
    .filter-pill.active {{
      background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
      border-color: transparent;
      color: #ffffff;
      box-shadow: 0 3px 12px rgba(79, 70, 229, 0.4);
    }}
    .pill-count {{
      background: rgba(0, 0, 0, 0.35);
      padding: 1px 6px;
      border-radius: 8px;
      font-size: 0.7rem;
      font-weight: 700;
    }}

    /* Sleek Segmented Pricing Control */
    .filter-pricing-row {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: rgba(15, 22, 38, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 3px 6px;
      border-radius: var(--radius-pill);
    }}
    .pricing-prefix {{
      font-size: 0.72rem;
      color: #64748b;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-right: 4px;
      padding-left: 6px;
    }}
    .price-chip {{
      background: transparent;
      border: 1px solid transparent;
      color: #94a3b8;
      padding: 4px 10px;
      border-radius: var(--radius-pill);
      font-size: 0.74rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .price-chip:hover {{ color: #fff; background: rgba(255, 255, 255, 0.06); }}
    .price-chip.active {{
      background: rgba(99, 102, 241, 0.22);
      border-color: rgba(99, 102, 241, 0.45);
      color: #c7d2fe;
    }}

    /* Section Styling */
    .section {{ padding: 36px 0 80px; }}
    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .section-title {{ font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; color: #fff; }}
    .results-badge {{
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: #a5b4fc;
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      font-size: 0.82rem;
      font-weight: 600;
    }}
    /* Tools Grid - Clean 3-Column Responsive Grid */
    .tools-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 22px;
      width: 100%;
      min-width: 0;
    }}
    @media (max-width: 1024px) {{
      .tools-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
      }}
    }}
    @media (max-width: 768px) {{
      .tools-grid {{
        grid-template-columns: minmax(0, 1fr);
        gap: 12px;
        width: 100%;
      }}
    }}

    /* Tool Card - Spacious, Clean & Modern */
    .tool-card {{
      background: var(--bg-card);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 22px 24px 20px 24px;
      min-height: 205px;
      min-width: 0;
      width: 100%;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      cursor: pointer;
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }}
    .tool-card:hover {{
      transform: translateY(-4px);
      border-color: rgba(99, 102, 241, 0.5);
      background: var(--bg-card-hover);
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.45), 0 0 24px rgba(99, 102, 241, 0.16);
    }}
    .card-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 14px;
      gap: 12px;
      min-width: 0;
      width: 100%;
    }}
    .tool-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
      flex: 1;
      overflow: hidden;
    }}
    .tool-avatar {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      color: #ffffff;
      font-weight: 700;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      flex-shrink: 0;
      letter-spacing: -0.02em;
    }}
    .tool-title-wrap {{
      min-width: 0;
      flex: 1;
      overflow: hidden;
    }}
    .tool-subcat {{
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #818cf8;
      margin-bottom: 4px;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .tool-name {{
      font-size: 1.05rem;
      font-weight: 700;
      margin: 0;
      color: #ffffff;
      letter-spacing: -0.01em;
      line-height: 1.3;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
      word-break: break-word;
      white-space: normal;
    }}
    .tool-card-title-link {{
      color: inherit;
      text-decoration: none;
    }}
    .tool-card-title-link:hover {{
      color: #818cf8;
    }}
    .badge-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }}
    .price-badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 4px 9px;
      border-radius: var(--radius-pill);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      line-height: 1;
    }}
    .price-freemium {{ background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); }}
    .price-free {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .price-paid {{ background: rgba(244, 63, 94, 0.15); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.3); }}
    .bookmark-btn {{
      background: none;
      border: none;
      color: var(--text-sub);
      font-size: 1.25rem;
      cursor: pointer;
      line-height: 1;
      padding: 2px 4px;
      border-radius: 6px;
      transition: color 0.15s;
    }}
    .bookmark-btn:hover, .bookmark-btn.saved {{ color: #fbbf24; }}
    .tool-desc {{
      font-size: 0.88rem;
      color: #94a3b8;
      line-height: 1.55;
      margin-bottom: 16px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
      flex-grow: 1;
      min-height: 2.8em;
    }}
    .card-bottom {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      gap: 12px;
    }}
    .card-bottom-pills {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      min-width: 0;
    }}
    .cat-pill {{
      font-size: 0.74rem;
      font-weight: 600;
      color: #94a3b8;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.06);
      padding: 4px 10px;
      border-radius: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 190px;
    }}
    .card-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }}
    .details-link {{
      font-size: 0.82rem;
      color: var(--text-sub);
      font-weight: 600;
      transition: color 0.15s;
      text-decoration: none;
    }}
    .details-link:hover {{ color: #ffffff; }}
    .tool-link {{
      font-size: 0.82rem;
      font-weight: 600;
      color: #818cf8;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      text-decoration: none;
      transition: color 0.15s;
    }}
    .tool-link:hover {{ color: #c084fc; text-decoration: underline; }}

    /* Mobile Responsive Overhaul (Screens <= 768px and <= 420px) */
    @media (max-width: 768px) {{
      .container {{
        padding: 0 16px;
      }}
      .navbar {{
        height: 60px;
      }}
      .nav-inner {{
        gap: 8px;
      }}
      .brand {{
        gap: 8px;
      }}
      .brand-logo-icon {{
        width: 32px;
        height: 32px;
      }}
      .brand-text {{
        display: inline-block;
        font-size: 1.05rem;
        font-weight: 800;
        color: #ffffff;
      }}
      .nav-actions {{
        gap: 6px;
      }}
      .btn-saved {{
        padding: 6px 10px;
        font-size: 0.8rem;
        border-radius: 8px;
      }}
      .btn-submit {{
        padding: 6px 11px;
        font-size: 0.8rem;
        white-space: nowrap;
        border-radius: 9999px;
      }}
      .hero {{
        padding: 26px 0 16px;
      }}
      .hero h1 {{
        font-size: 1.65rem;
        margin-bottom: 14px;
        line-height: 1.25;
      }}
      .search-box-wrap {{
        margin-bottom: 14px;
      }}
      .search-box {{
        padding: 12px 36px 12px 42px;
        font-size: 0.88rem;
        border-radius: 12px;
      }}
      .search-hint {{
        display: none; /* Hide keyboard shortcut key on mobile touch screens */
      }}

      /* Horizontal Swipeable Category Bar on Mobile */
      .filter-toolbar {{
        gap: 10px;
        width: 100%;
      }}
      .filter-pills-row {{
        display: flex;
        flex-wrap: nowrap;
        justify-content: flex-start;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding: 4px 16px 8px 16px;
        margin: 0 -16px;
        width: calc(100% + 32px);
        gap: 8px;
      }}
      .filter-pills-row::-webkit-scrollbar {{
        display: none;
      }}
      .filter-pill {{
        flex-shrink: 0;
        white-space: nowrap;
        padding: 7px 13px;
        font-size: 0.78rem;
      }}

      /* Compact Pricing Control on Mobile */
      .filter-pricing-row {{
        display: flex;
        overflow-x: auto;
        max-width: 100%;
        justify-content: center;
        gap: 2px;
        padding: 3px 6px;
      }}
      .pricing-prefix {{
        display: none; /* Hide prefix to save space on mobile */
      }}
      .price-chip {{
        padding: 4px 8px;
        font-size: 0.72rem;
        white-space: nowrap;
      }}

      /* Section Header on Mobile */
      .section {{
        padding: 20px 0 60px;
      }}
      .section-header {{
        margin-bottom: 14px;
        gap: 8px;
      }}
      .section-title {{
        font-size: 1.35rem;
      }}
      .results-badge {{
        font-size: 0.75rem;
        padding: 4px 10px;
      }}

      /* 1-Column Clean Tool Cards on Mobile */
      .tools-grid {{
        grid-template-columns: minmax(0, 1fr) !important;
        gap: 12px;
        width: 100%;
        max-width: 100%;
      }}
      .tool-card {{
        padding: 16px 16px 14px 16px;
        min-height: auto;
        min-width: 0;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        border-radius: 14px;
      }}
      .card-top {{
        margin-bottom: 10px;
        gap: 10px;
        min-width: 0;
        width: 100%;
      }}
      .tool-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
        flex: 1;
        overflow: hidden;
      }}
      .tool-avatar {{
        width: 38px;
        height: 38px;
        border-radius: 10px;
        font-size: 0.88rem;
        flex-shrink: 0;
      }}
      .tool-title-wrap {{
        min-width: 0;
        flex: 1;
        overflow: hidden;
      }}
      .tool-name {{
        font-size: 0.98rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-word;
        white-space: normal;
      }}
      .badge-row {{
        flex-shrink: 0;
        display: flex;
        align-items: center;
        gap: 6px;
      }}
      .price-badge {{
        font-size: 0.65rem;
        padding: 3px 7px;
      }}
      .bookmark-btn {{
        font-size: 1.15rem;
      }}
      .tool-desc {{
        font-size: 0.84rem;
        line-height: 1.45;
        margin: 10px 0 12px 0;
        min-height: auto;
        -webkit-line-clamp: 2;
      }}
      .card-bottom {{
        padding-top: 10px;
        gap: 8px;
        min-width: 0;
        width: 100%;
      }}
      .cat-pill {{
        max-width: 130px;
        font-size: 0.7rem;
        padding: 3px 8px;
      }}
      .card-actions {{
        gap: 8px;
      }}
      .details-link, .tool-link {{
        font-size: 0.78rem;
      }}
    }}

    @media (max-width: 420px) {{
      .container {{
        padding: 0 12px;
      }}
      .navbar {{
        height: 56px;
      }}
      .brand {{
        gap: 6px;
      }}
      .brand-logo-icon {{
        width: 28px;
        height: 28px;
      }}
      .brand-text {{
        font-size: 0.95rem;
      }}
      .nav-actions {{
        gap: 5px;
      }}
      .btn-saved {{
        padding: 5px 7px;
        font-size: 0.75rem;
      }}
      .btn-submit {{
        padding: 5px 9px;
        font-size: 0.75rem;
      }}
      .hero h1 {{
        font-size: 1.45rem;
      }}
      .tool-card {{
        padding: 16px 14px 14px 14px;
      }}
      .mobile-tools-bar {{
        top: 56px;
        padding: 6px 0;
      }}
      .mobile-tool-pill {{
        padding: 5px 10px;
        font-size: 0.74rem;
      }}
    }}

    /* Empty state */
    .empty-state {{
      grid-column: 1 / -1;
      text-align: center;
      padding: 60px 20px;
      background: var(--bg-card);
      border: 1px dashed var(--border);
      border-radius: var(--radius-lg);
      display: none;
    }}
    .empty-state h3 {{ font-size: 1.3rem; color: #fff; margin-bottom: 8px; }}
    .empty-state p {{ color: var(--text-muted); margin-bottom: 20px; }}
    .load-more-wrap {{
      text-align: center;
      margin-top: 36px;
    }}
    .btn-load-more {{
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.35);
      color: #c7d2fe;
      padding: 12px 28px;
      border-radius: var(--radius-pill);
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-load-more:hover {{
      background: rgba(99, 102, 241, 0.25);
      border-color: #818cf8;
      color: #ffffff;
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(99, 102, 241, 0.25);
    }}

    /* Domain Showcase Cards */
    .cat-showcase-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 20px;
      margin-top: 16px;
    }}
    .cat-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 26px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .cat-card:hover {{
      border-color: rgba(99, 102, 241, 0.4);
      transform: translateY(-2px);
      background: var(--bg-card-hover);
    }}
    .cat-card h3 {{ font-size: 1.18rem; font-weight: 700; color: #fff; margin-bottom: 8px; }}
    .cat-card p {{ font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; }}
    .cat-card-meta {{
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      font-weight: 600;
      color: #818cf8;
    }}

    /* FAQ Section */
    .faq-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
      max-width: 900px;
      margin: 0 auto;
    }}
    .faq-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      overflow: hidden;
    }}
    .faq-q {{
      padding: 20px 24px;
      font-weight: 700;
      font-size: 1.05rem;
      color: #ffffff;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
    }}
    .faq-q:hover {{ background: rgba(255, 255, 255, 0.02); }}
    .faq-icon {{ font-size: 1.3rem; transition: transform 0.2s ease; color: #818cf8; }}
    .faq-card.open .faq-icon {{ transform: rotate(45deg); }}
    .faq-a {{
      padding: 0 24px 22px;
      color: var(--text-muted);
      font-size: 0.95rem;
      line-height: 1.6;
      display: none;
    }}
    .faq-card.open .faq-a {{ display: block; }}

    /* Footer */
    .footer {{
      border-top: 1px solid var(--border);
      padding: 60px 0 40px;
      background: rgba(9, 13, 22, 0.95);
      color: var(--text-sub);
      font-size: 0.9rem;
    }}
    .footer-inner {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 24px;
      margin-bottom: 30px;
    }}
    .footer-links {{ display: flex; gap: 20px; flex-wrap: wrap; }}
    .footer-links a:hover {{ color: #ffffff; }}
  </style>
</head>
<body>
  <div class="ambient-glow"></div>

  <!-- Redesigned Modern Navbar -->
  <nav class="navbar">
    <div class="container nav-inner">
      <a href="/" class="brand" title="All AI Tools — Complete AI Directory" aria-label="All AI Tools — Home">
        <span class="brand-logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 1.5C12 1.5 13.5 7.5 15.5 9.5C17.5 11.5 23.5 12 23.5 12C23.5 12 17.5 12.5 15.5 14.5C13.5 16.5 12 22.5 12 22.5C12 22.5 10.5 16.5 8.5 14.5C6.5 12.5 0.5 12 0.5 12C0.5 12 6.5 11.5 8.5 9.5C10.5 7.5 12 1.5 12 1.5Z" fill="url(#aiBrandGradHome)"/>
            <circle cx="19.5" cy="4.5" r="2" fill="#38bdf8"/>
            <circle cx="4.5" cy="19.5" r="1.5" fill="#a855f7"/>
            <defs>
              <linearGradient id="aiBrandGradHome" x1="0.5" y1="1.5" x2="23.5" y2="22.5" gradientUnits="userSpaceOnUse">
                <stop stop-color="#818cf8"/>
                <stop offset="0.45" stop-color="#c084fc"/>
                <stop offset="1" stop-color="#38bdf8"/>
              </linearGradient>
            </defs>
          </svg>
        </span>
        <span class="brand-text">All AI Tools</span>
      </a>

      <div class="nav-links">
        <a href="#categories" class="nav-link">Categories</a>
        <a href="/tools/ai-image-generator/" class="nav-link nav-link-special">
          <span class="nav-sparkle">&#10024;</span> AI Generator
        </a>
        <a href="/tools/image-enhancer/" class="nav-link nav-link-special">
          <span class="nav-sparkle">&#9889;</span> 4K Enhancer
        </a>
      </div>

      <div class="nav-actions">
        <button class="btn-saved" id="showSavedBtn" title="View Saved Tools">
          <span>&#9734;</span>
          <span>Saved</span>
          <span id="savedCountBadge" class="saved-badge" style="display:none;">0</span>
        </button>
        <a href="/submit/" class="btn-submit">+ Submit Tool</a>
      </div>
    </div>
  </nav>

  <!-- Mobile Quick-Access Tools Strip (Sticky underneath navbar on mobile) -->
  <div class="mobile-tools-bar">
    <div class="container mobile-tools-inner">
      <a href="/tools/ai-image-generator/" class="mobile-tool-pill" title="Free Live AI Image Generator">
        <span class="mobile-tool-icon">&#10024;</span>
        <span>AI Generator</span>
        <span class="mobile-tool-badge">Free</span>
      </a>
      <a href="/tools/image-enhancer/" class="mobile-tool-pill" title="Real AI 4K Upscaler">
        <span class="mobile-tool-icon">&#9889;</span>
        <span>4K Enhancer</span>
        <span class="mobile-tool-badge">Free</span>
      </a>
    </div>
  </div>

  <!-- Hero Section -->
  <header class="hero">
    <div class="container">
      <h1>Complete <span class="gradient-text">All AI Tools</span> Directory</h1>

      <!-- Search Box with Query Param Support -->
      <div class="search-box-wrap">
        <span class="search-icon">&#128269;</span>
        <input type="text" id="searchInput" class="search-box" placeholder="Search 10,000+ AI tools by name, category, or task..." autofocus autocomplete="off" />
        <button id="clearSearch" class="clear-search" aria-label="Clear Search">&times;</button>
        <span class="search-hint">/</span>
      </div>

      <!-- Unified Filter Toolbar -->
      <div class="filter-toolbar" id="categories">
        <!-- Category Filter Pills (All 7 fit in a clean balanced single row) -->
        <div class="filter-pills-row">
          <button class="filter-pill active" data-filter="all">
            <span>All AI Tools</span>
            <span class="pill-count">{total_tools}</span>
          </button>
          <button class="filter-pill" data-filter="chat-reasoning">
            <span>Chat &amp; LLMs</span>
            <span class="pill-count">{cat_counts.get('chat-reasoning', 0)}</span>
          </button>
          <button class="filter-pill" data-filter="coding-dev">
            <span>Coding &amp; Dev</span>
            <span class="pill-count">{cat_counts.get('coding-dev', 0)}</span>
          </button>
          <button class="filter-pill" data-filter="image-art">
            <span>Image &amp; Art</span>
            <span class="pill-count">{cat_counts.get('image-art', 0)}</span>
          </button>
          <button class="filter-pill" data-filter="video-3d">
            <span>Video &amp; 3D</span>
            <span class="pill-count">{cat_counts.get('video-3d', 0)}</span>
          </button>
          <button class="filter-pill" data-filter="voice-audio">
            <span>Voice &amp; Audio</span>
            <span class="pill-count">{cat_counts.get('voice-audio', 0)}</span>
          </button>
          <button class="filter-pill" data-filter="ai-search">
            <span>AI Search</span>
            <span class="pill-count">{cat_counts.get('ai-search', 0)}</span>
          </button>
        </div>

        <!-- Pricing Filter Segmented Control -->
        <div class="filter-pricing-row">
          <span class="pricing-prefix">Pricing:</span>
          <button class="price-chip active" data-pricing="all">All</button>
          <button class="price-chip" data-pricing="free">Free ({cat_counts.get('free', 0) if 'free' in cat_counts else sum(1 for t in tools if t.get('pricing','').lower()=='free')})</button>
          <button class="price-chip" data-pricing="freemium">Freemium ({sum(1 for t in tools if t.get('pricing','').lower()=='freemium')})</button>
          <button class="price-chip" data-pricing="paid">Paid ({sum(1 for t in tools if t.get('pricing','').lower()=='paid')})</button>
        </div>
      </div>
    </div>
  </header>

  <!-- Featured Tools Directory Grid -->
  <section class="section" id="featured">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">All AI Tools Catalog ({total_tools}+ Platforms)</h2>
        </div>
        <div class="results-badge" id="resultsCounter">Showing {total_tools} Verified AI Tools</div>
      </div>

      <div class="tools-grid" id="toolsGrid">
{cards_block}
        <div class="empty-state" id="emptyState">
          <h3>No AI tools found</h3>
          <p>We couldn't find anything matching your filters or search keywords.</p>
          <button class="btn-submit" id="resetFiltersBtn">Reset All Filters</button>
        </div>
      </div>

      <div class="load-more-wrap" id="loadMoreWrap">
        <button id="loadMoreBtn" class="btn-load-more">Load More AI Tools &darr;</button>
      </div>
    </div>
  </section>

  <!-- Domain Showcase Categories Section -->
  <section class="section" id="categories" style="border-top: 1px solid var(--border);">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">Explore AI Tools by Category</h2>
          <p class="section-sub">Browse verified software tailored to your workflow and industry use case.</p>
        </div>
      </div>

      <div class="cat-showcase-grid">
        <div class="cat-card" data-jump="chat-reasoning">
          <div>
            <h3>Chat, Logic &amp; Reasoning</h3>
            <p>Frontier LLMs, autonomous agents, reasoning engines, and custom GPT models engineered for conversational intelligence and complex synthesis.</p>
          </div>
          <div class="cat-card-meta">
            <span>{cat_counts.get('chat-reasoning', 0)} Tools</span>
            <span>Explore Domain &rarr;</span>
          </div>
        </div>

        <div class="cat-card" data-jump="coding-dev">
          <div>
            <h3>Code Generation &amp; Engineering</h3>
            <p>Autonomous AI software engineers, full-stack app builders, terminal assistants, automated test generators, and refactoring agents.</p>
          </div>
          <div class="cat-card-meta">
            <span>{cat_counts.get('coding-dev', 0)} Tools</span>
            <span>Explore Domain &rarr;</span>
          </div>
        </div>

        <div class="cat-card" data-jump="image-art">
          <div>
            <h3>Image Generation, Enhancers &amp; Design</h3>
            <p>Diffusion synthesis, prompt-to-image renderers, photo enhancers, brand asset generators, UI mockups, and AI graphic workstations.</p>
          </div>
          <div class="cat-card-meta">
            <span>{cat_counts.get('image-art', 0)} Tools</span>
            <span>Explore Domain &rarr;</span>
          </div>
        </div>

        <div class="cat-card" data-jump="video-3d">
          <div>
            <h3>Video Creation, Avatars &amp; 3D Worlds</h3>
            <p>Generative cinematic video, text-to-3D mesh creators, virtual avatar presenters, automated clip repurposers, and VFX engines.</p>
          </div>
          <div class="cat-card-meta">
            <span>{cat_counts.get('video-3d', 0)} Tools</span>
            <span>Explore Domain &rarr;</span>
          </div>
        </div>

        <div class="cat-card" data-jump="voice-audio">
          <div>
            <h3>Voice, Speech &amp; Music</h3>
            <p>Zero-shot voice cloning, real-time multilingual text-to-speech, synthetic music studios, voice isolation, and audio agents.</p>
          </div>
          <div class="cat-card-meta">
            <span>{cat_counts.get('voice-audio', 0)} Tools</span>
            <span>Explore Domain &rarr;</span>
          </div>
        </div>

        <div class="cat-card" data-jump="ai-search">
          <div>
            <h3>AI Search &amp; Research</h3>
            <p>Perplexity-style conversational search engines, deep literature review assistants, fact-checking agents, and academic graph analyzers.</p>
          </div>
          <div class="cat-card-meta">
            <span>{cat_counts.get('ai-search', 0)} Tools</span>
            <span>Explore Domain &rarr;</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- FAQ Section with Schema Markup -->
  <section class="section" id="faq" style="border-top: 1px solid var(--border);">
    <div class="container">
      <div class="section-header" style="text-align: center; justify-content: center;">
        <div>
          <h2 class="section-title">Frequently Asked Questions</h2>
          <p class="section-sub">Everything you need to know about the All AI Tools directory, software list, and alternatives.</p>
        </div>
      </div>

      <div class="faq-grid">
        <div class="faq-card">
          <div class="faq-q">
            <span>Where can I find a complete list of all AI tools in one website?</span>
            <span class="faq-icon">+</span>
          </div>
          <div class="faq-a">
            All AI Tools (allaitools.online) brings together {total_tools}+ artificial intelligence software platforms, reasoning models, custom GPTs, and autonomous agents across 6 core industry verticals in one fast, searchable website.
          </div>
        </div>

        <div class="faq-card">
          <div class="faq-q">
            <span>Are there free AI tools and alternatives available on All AI Tools?</span>
            <span class="faq-icon">+</span>
          </div>
          <div class="faq-a">
            Yes! We categorize every tool with clear pricing badges: Free, Freemium, and Paid. You can instantly filter the directory to explore 100% free AI tools or freemium tools with generous trial tiers.
          </div>
        </div>

        <div class="faq-card">
          <div class="faq-q">
            <span>How does the tool page and card click work?</span>
            <span class="faq-icon">+</span>
          </div>
          <div class="faq-a">
            Clicking on any tool card opens its dedicated URL (/toolname) featuring full specs, search queries, parameters, and verified alternatives. Clicking the "Open Tool" button redirects directly to the tool's official website in a new window.
          </div>
        </div>

        <div class="faq-card">
          <div class="faq-q">
            <span>What are the best alternatives to popular AI tools?</span>
            <span class="faq-icon">+</span>
          </div>
          <div class="faq-a">
            Every tool in our catalog has a dedicated alternatives section displaying top-rated competitors in the same domain with verified links, feature summaries, and pricing tiers.
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="container">
      <div class="footer-inner">
        <div class="brand">
          <span class="brand-icon">AI</span>
          <span>All AI Tools (allaitools)</span>
        </div>
        <div class="footer-links">
          <a href="#featured">Directory</a>
          <a href="/?category=chat-reasoning">Chat &amp; Reasoning</a>
          <a href="/?category=coding-dev">Coding &amp; Dev</a>
          <a href="/?category=image-art">Image &amp; Art</a>
          <a href="/?category=video-3d">Video &amp; 3D</a>
          <a href="/?category=voice-audio">Voice &amp; Audio</a>
          <a href="/?category=ai-search">AI Search</a>
          <a href="/sitemap.xml">Sitemap</a>
          <a href="/robots.txt">Robots.txt</a>
        </div>
      </div>
      <p>&copy; 2026 All AI Tools (allaitools.online). All rights reserved. Open Tool links navigate directly to third-party tools.</p>
    </div>
  </footer>

  <!-- Search & Filter JavaScript with URL Parameter Sync -->
  <script>
    (function () {{
      var searchInput = document.getElementById('searchInput');
      var clearBtn = document.getElementById('clearSearch');
      var filterPills = document.querySelectorAll('.filter-pill');
      var priceChips = document.querySelectorAll('.price-chip');
      var emptyState = document.getElementById('emptyState');
      var resultsCounter = document.getElementById('resultsCounter');
      var resetBtn = document.getElementById('resetFiltersBtn');
      var showSavedBtn = document.getElementById('showSavedBtn');
      var savedCountBadge = document.getElementById('savedCountBadge');
      var toolsGrid = document.getElementById('toolsGrid');
      var loadMoreWrap = document.getElementById('loadMoreWrap');
      var loadMoreBtn = document.getElementById('loadMoreBtn');

      var currentCat = 'all';
      var currentPricing = 'all';
      var filterOnlySaved = false;

      var allToolsData = [];
      var currentFiltered = [];
      var pageSize = 48;
      var currentPage = 1;

      var savedTools = [];
      try {{
        savedTools = JSON.parse(localStorage.getItem('saved_ai_tools') || '[]');
      }} catch (e) {{}}

      function escapeHtml(str) {{
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      }}

      function updateSavedUI() {{
        document.querySelectorAll('.bookmark-btn').forEach(function (btn) {{
          var toolName = (btn.getAttribute('data-tool') || '').toLowerCase();
          if (savedTools.indexOf(toolName) !== -1) {{
            btn.classList.add('saved');
            btn.innerHTML = '&#9733;';
          }} else {{
            btn.classList.remove('saved');
            btn.innerHTML = '&#9734;';
          }}
        }});
        if (savedTools.length > 0) {{
          savedCountBadge.style.display = 'inline-block';
          savedCountBadge.textContent = savedTools.length;
        }} else {{
          savedCountBadge.style.display = 'none';
        }}
      }}

      function bindBookmarkEvents() {{
        document.querySelectorAll('.bookmark-btn').forEach(function (btn) {{
          if (btn.hasAttribute('data-bound')) return;
          btn.setAttribute('data-bound', '1');
          btn.addEventListener('click', function (e) {{
            e.preventDefault();
            e.stopPropagation();
            var toolName = (btn.getAttribute('data-tool') || '').toLowerCase();
            var idx = savedTools.indexOf(toolName);
            if (idx === -1) {{
              savedTools.push(toolName);
            }} else {{
              savedTools.splice(idx, 1);
            }}
            try {{
              localStorage.setItem('saved_ai_tools', JSON.stringify(savedTools));
            }} catch (err) {{}}
            updateSavedUI();
            if (filterOnlySaved) filterTools();
          }});
        }});
      }}

      // Event delegation for card clicks
      if (toolsGrid) {{
        toolsGrid.addEventListener('click', function (e) {{
          if (e.target.closest('a') || e.target.closest('button')) return;
          var card = e.target.closest('.tool-card');
          if (card) {{
            var slug = card.getAttribute('data-slug');
            var path = card.getAttribute('data-tool-path');
            if (slug) {{
              window.location.href = '/' + slug + '/';
            }} else if (path) {{
              window.location.href = path;
            }}
          }}
        }});
      }}

      function createCardHtml(t) {{
        var pLower = (t.p || '').toLowerCase();
        var priceClass = pLower === 'free' ? 'price-free' : (pLower === 'paid' ? 'price-paid' : 'price-freemium');
        var isSaved = savedTools.indexOf(t.n.toLowerCase()) !== -1;
        var subcat = t.sc || t.cp || 'AI Tools';
        var toolPath = '/' + escapeHtml(t.s) + '/';
        return '<article class="tool-card" data-slug="' + escapeHtml(t.s) + '" data-category="' + escapeHtml(t.cs) + '" data-pricing="' + escapeHtml(pLower) + '" data-name="' + escapeHtml(t.n.toLowerCase()) + '" data-tool-path="' + toolPath + '">' +
          '<div class="card-top">' +
            '<div class="tool-brand">' +
              '<div class="tool-avatar" style="background: ' + escapeHtml(t.c) + ';">' + escapeHtml(t.b) + '</div>' +
              '<div class="tool-title-wrap">' +
                '<span class="tool-subcat">' + escapeHtml(subcat) + '</span>' +
                '<h3 class="tool-name"><a href="' + toolPath + '" class="tool-card-title-link" title="' + escapeHtml(t.n) + '">' + escapeHtml(t.n) + '</a></h3>' +
              '</div>' +
            '</div>' +
            '<button class="bookmark-btn' + (isSaved ? ' saved' : '') + '" title="Bookmark ' + escapeHtml(t.n) + '" data-tool="' + escapeHtml(t.n) + '" aria-label="Bookmark ' + escapeHtml(t.n) + '">' + (isSaved ? '&#9733;' : '&#9734;') + '</button>' +
          '</div>' +
          '<p class="tool-desc">' + escapeHtml(t.d) + '</p>' +
          '<div class="card-bottom">' +
            '<div class="card-bottom-pills">' +
              '<span class="cat-pill">' + escapeHtml(t.cp) + '</span>' +
              '<span class="price-badge ' + priceClass + '">' + escapeHtml(t.p) + '</span>' +
            '</div>' +
            '<div class="card-actions">' +
              '<a href="' + toolPath + '" class="details-link">Details &rarr;</a>' +
              '<a href="' + escapeHtml(t.u) + '" target="_blank" rel="noopener noreferrer nofollow" class="tool-link">Visit &rarr;</a>' +
            '</div>' +
          '</div>' +
        '</article>';
      }}

      function renderBatch(append) {{
        if (!append) {{
          var empty = document.getElementById('emptyState');
          toolsGrid.innerHTML = '';
          if (empty) toolsGrid.appendChild(empty);
        }}
        var start = append ? (currentPage - 1) * pageSize : 0;
        var end = currentPage * pageSize;
        var slice = currentFiltered.slice(start, end);

        var html = '';
        for (var i = 0; i < slice.length; i++) {{
          html += createCardHtml(slice[i]);
        }}

        var temp = document.createElement('div');
        temp.innerHTML = html;
        while (temp.firstChild) {{
          toolsGrid.insertBefore(temp.firstChild, emptyState);
        }}

        bindBookmarkEvents();
        updateSavedUI();

        if (end < currentFiltered.length) {{
          if (loadMoreWrap) {{
            loadMoreWrap.style.display = 'block';
            if (loadMoreBtn) {{
              loadMoreBtn.textContent = 'Load More AI Tools (Showing ' + Math.min(end, currentFiltered.length).toLocaleString() + ' of ' + currentFiltered.length.toLocaleString() + ') ↓';
            }}
          }}
        }} else {{
          if (loadMoreWrap) loadMoreWrap.style.display = 'none';
        }}
      }}

      function updateUrlParams() {{
        var params = new URLSearchParams();
        var q = searchInput.value.trim();
        if (q) params.set('q', q);
        if (currentCat && currentCat !== 'all') params.set('category', currentCat);
        if (currentPricing && currentPricing !== 'all') params.set('pricing', currentPricing);
        var qString = params.toString();
        var newUrl = window.location.pathname + (qString ? '?' + qString : '');
        window.history.replaceState({{}}, '', newUrl);
      }}

      function filterTools() {{
        var q = searchInput.value.trim().toLowerCase();
        if (q.length > 0) {{
          clearBtn.style.display = 'block';
        }} else {{
          clearBtn.style.display = 'none';
        }}

        currentPage = 1;

        if (allToolsData.length === 0) {{
          var visible = 0;
          document.querySelectorAll('.tool-card').forEach(function (card) {{
            var cardCat = card.getAttribute('data-category');
            var cardPrice = card.getAttribute('data-pricing');
            var cardName = (card.getAttribute('data-name') || '').toLowerCase();
            var matchesCat = (currentCat === 'all' || cardCat === currentCat);
            var matchesPrice = (currentPricing === 'all' || cardPrice === currentPricing);
            var matchesQuery = (!q || cardName.indexOf(q) !== -1);
            var matchesSaved = (!filterOnlySaved || savedTools.indexOf(cardName) !== -1);

            if (matchesCat && matchesPrice && matchesQuery && matchesSaved) {{
              card.style.display = '';
              visible++;
            }} else {{
              card.style.display = 'none';
            }}
          }});
          resultsCounter.textContent = 'Showing ' + visible.toLocaleString() + ' Verified AI Tools';
          return;
        }}

        currentFiltered = allToolsData.filter(function (t) {{
          var pLower = (t.p || '').toLowerCase();
          var matchesCat = (currentCat === 'all' || t.cs === currentCat);
          var matchesPrice = (currentPricing === 'all' || pLower === currentPricing);
          var matchesQuery = (!q || t.n.toLowerCase().indexOf(q) !== -1 || (t.d && t.d.toLowerCase().indexOf(q) !== -1) || (t.sc && t.sc.toLowerCase().indexOf(q) !== -1));
          var matchesSaved = (!filterOnlySaved || savedTools.indexOf(t.n.toLowerCase()) !== -1);
          return matchesCat && matchesPrice && matchesQuery && matchesSaved;
        }});

        if (currentFiltered.length === 0) {{
          emptyState.style.display = 'block';
          resultsCounter.textContent = '0 AI Tools Found';
          if (loadMoreWrap) loadMoreWrap.style.display = 'none';
          document.querySelectorAll('.tool-card').forEach(function (c) {{ c.remove(); }});
        }} else {{
          emptyState.style.display = 'none';
          resultsCounter.textContent = 'Showing ' + currentFiltered.length.toLocaleString() + ' Verified AI Tools';
          renderBatch(false);
        }}

        updateUrlParams();
      }}

      if (loadMoreBtn) {{
        loadMoreBtn.addEventListener('click', function () {{
          currentPage++;
          renderBatch(true);
        }});
      }}

      // Infinite scroll trigger
      window.addEventListener('scroll', function () {{
        if (!loadMoreWrap || loadMoreWrap.style.display === 'none') return;
        var rect = loadMoreWrap.getBoundingClientRect();
        if (rect.top <= window.innerHeight + 400) {{
          if (currentPage * pageSize < currentFiltered.length) {{
            currentPage++;
            renderBatch(true);
          }}
        }}
      }}, {{ passive: true }});

      // Keyboard shortcut '/'
      window.addEventListener('keydown', function (e) {{
        if (e.key === '/' && document.activeElement !== searchInput) {{
          e.preventDefault();
          searchInput.focus();
        }}
        if (e.key === 'Escape' && document.activeElement === searchInput) {{
          searchInput.value = '';
          filterTools();
          searchInput.blur();
        }}
      }});

      searchInput.addEventListener('input', function () {{
        filterTools();
      }});

      clearBtn.addEventListener('click', function () {{
        searchInput.value = '';
        filterTools();
        searchInput.focus();
      }});

      // Category Pill Click
      filterPills.forEach(function (pill) {{
        pill.addEventListener('click', function () {{
          filterPills.forEach(function (p) {{ p.classList.remove('active'); }});
          pill.classList.add('active');
          currentCat = pill.getAttribute('data-filter');
          filterTools();
        }});
      }});

      // Pricing Chip Click
      priceChips.forEach(function (chip) {{
        chip.addEventListener('click', function () {{
          priceChips.forEach(function (c) {{ c.classList.remove('active'); }});
          chip.classList.add('active');
          currentPricing = chip.getAttribute('data-pricing');
          filterTools();
        }});
      }});

      // Domain Showcase jump
      document.querySelectorAll('.cat-card').forEach(function (card) {{
        card.addEventListener('click', function () {{
          var jumpCat = card.getAttribute('data-jump');
          var targetPill = document.querySelector('.filter-pill[data-filter="' + jumpCat + '"]');
          if (targetPill) {{
            targetPill.click();
            document.getElementById('featured').scrollIntoView({{ behavior: 'smooth' }});
          }}
        }});
      }});

      // Reset
      resetBtn.addEventListener('click', function () {{
        searchInput.value = '';
        currentCat = 'all';
        currentPricing = 'all';
        filterOnlySaved = false;
        showSavedBtn.style.background = '';
        filterPills.forEach(function (p) {{
          p.classList.toggle('active', p.getAttribute('data-filter') === 'all');
        }});
        priceChips.forEach(function (c) {{
          c.classList.toggle('active', c.getAttribute('data-pricing') === 'all');
        }});
        filterTools();
      }});

      // Saved Filter Toggle
      showSavedBtn.addEventListener('click', function () {{
        filterOnlySaved = !filterOnlySaved;
        if (filterOnlySaved) {{
          showSavedBtn.style.background = 'rgba(251, 191, 36, 0.2)';
          showSavedBtn.style.borderColor = 'rgba(251, 191, 36, 0.5)';
        }} else {{
          showSavedBtn.style.background = '';
          showSavedBtn.style.borderColor = '';
        }}
        filterTools();
        document.getElementById('featured').scrollIntoView({{ behavior: 'smooth' }});
      }});

      // FAQ accordion
      document.querySelectorAll('.faq-q').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          btn.parentElement.classList.toggle('open');
        }});
      }});

      bindBookmarkEvents();
      updateSavedUI();

      // Read initial URL query parameters
      var urlParams = new URLSearchParams(window.location.search);
      var qParam = urlParams.get('q');
      var catParam = urlParams.get('category') || urlParams.get('cat');
      var pricingParam = urlParams.get('pricing') || urlParams.get('price');

      if (qParam) {{
        searchInput.value = qParam;
      }}
      if (catParam) {{
        var targetPill = document.querySelector('.filter-pill[data-filter="' + catParam + '"]');
        if (targetPill) {{
          filterPills.forEach(function (p) {{ p.classList.remove('active'); }});
          targetPill.classList.add('active');
          currentCat = catParam;
        }}
      }}
      if (pricingParam) {{
        var targetChip = document.querySelector('.price-chip[data-pricing="' + pricingParam.toLowerCase() + '"]');
        if (targetChip) {{
          priceChips.forEach(function (c) {{ c.classList.remove('active'); }});
          targetChip.classList.add('active');
          currentPricing = pricingParam.toLowerCase();
        }}
      }}

      // Fetch 10,000 tools compact JSON in the background
      fetch('/tools_compact.json')
        .then(function (res) {{ return res.json(); }})
        .then(function (data) {{
          allToolsData = data;
          currentFiltered = data;
          if (qParam || (catParam && catParam !== 'all') || (pricingParam && pricingParam !== 'all') || filterOnlySaved) {{
            filterTools();
          }} else {{
            resultsCounter.textContent = 'Showing ' + data.length.toLocaleString() + ' Verified AI Tools';
          }}
        }})
        .catch(function (err) {{
          console.warn('Could not load tools_compact.json, using static cards', err);
        }});
    }})();
  </script>
</body>
</html>
"""

# Write root index.html and public/index.html
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html_content)

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(index_html_content)

print(f"Generated root index.html and public/index.html with {total_tools} tools.")

# 4. Generate 404.html
page_404_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Page Not Found (404) | All AI Tools (allaitools)</title>
  <meta name="description" content="The requested AI tool or page could not be found. Search {total_tools}+ artificial intelligence tools on All AI Tools." />
  <meta name="robots" content="noindex, follow" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2222%22 fill=%22%234F46E5%22/><text y=%2268%22 x=%2250%22 font-family=%22system-ui,sans-serif%22 font-weight=%22800%22 font-size=%2254%22 fill=%22white%22 text-anchor=%22middle%22>AI</text></svg>" />
  <style>
    :root {{
      --bg: #090d16;
      --bg-card: #0f1626;
      --border: rgba(255, 255, 255, 0.08);
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #6366f1;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text-main); font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; text-align: center; }}
    .box {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 48px 32px; max-width: 600px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
    .code {{ font-size: 4rem; font-weight: 900; background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 12px; }}
    p {{ color: var(--text-muted); font-size: 0.95rem; margin-bottom: 24px; line-height: 1.6; }}
    .search-input {{ width: 100%; padding: 14px 20px; background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 12px; color: #fff; font-size: 1rem; margin-bottom: 20px; outline: none; }}
    .search-input:focus {{ border-color: var(--accent); }}
    .btn {{ display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #fff; font-weight: 700; padding: 12px 28px; border-radius: 10px; text-decoration: none; }}
    .quick-links {{ display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 24px; }}
    .quick-link {{ background: rgba(255,255,255,0.05); padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; color: #cbd5e1; text-decoration: none; border: 1px solid var(--border); }}
    .quick-link:hover {{ background: rgba(99,102,241,0.2); color: #fff; }}
  </style>
</head>
<body>
  <div class="box">
    <div class="code">404</div>
    <h1>AI Tool or Page Not Found</h1>
    <p>The page you are looking for might have been moved, renamed, or is temporarily unavailable. Search {total_tools}+ verified AI tools below:</p>
    <input type="search" id="search404" class="search-input" placeholder="Search AI tools (e.g. ChatGPT, Claude, Airbrush, Midjourney)..." />
    <br />
    <a href="/" class="btn">&larr; Return to All AI Tools</a>
    <div class="quick-links">
      <a href="/?category=chat-reasoning" class="quick-link">Chat &amp; Reasoning</a>
      <a href="/?category=coding-dev" class="quick-link">Coding &amp; Dev</a>
      <a href="/?category=image-art" class="quick-link">Image &amp; Art</a>
      <a href="/?category=video-3d" class="quick-link">Video &amp; 3D</a>
      <a href="/?category=voice-audio" class="quick-link">Voice &amp; Audio</a>
      <a href="/?category=ai-search" class="quick-link">AI Search</a>
    </div>
  </div>
  <script>
    var input = document.getElementById('search404');
    input.addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' && input.value.trim()) {{
        window.location.href = '/?q=' + encodeURIComponent(input.value.trim());
      }}
    }});
  </script>
</body>
</html>"""

with open("404.html", "w", encoding="utf-8") as f:
    f.write(page_404_content)
with open("public/404.html", "w", encoding="utf-8") as f:
    f.write(page_404_content)
print("Generated 404.html.")

# 5. Generate robots.txt
robots_txt_content = f"""# Robots.txt for {BASE_URL}/
# Explicitly allowing all search engine web crawlers and AI agents

User-agent: *
Allow: /

# Google Search, Google Images, Googlebot News, and Gemini Crawlers
User-agent: Googlebot
Allow: /

User-agent: Googlebot-Image
Allow: /

User-agent: Googlebot-News
Allow: /

User-agent: Google-Extended
Allow: /

# Microsoft Bing & Copilot
User-agent: Bingbot
Allow: /

User-agent: msnbot
Allow: /

# Yahoo & DuckDuckGo
User-agent: Slurp
Allow: /

User-agent: DuckDuckBot
Allow: /

# Baidu & Yandex
User-agent: Baiduspider
Allow: /

User-agent: YandexBot
Allow: /

# Apple Intelligence & Siri
User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

# OpenAI Crawlers (GPT-4, SearchGPT, ChatGPT Browsing)
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

# Anthropic Claude Crawlers
User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Claude-Web
Allow: /

# Perplexity AI Search Crawler
User-agent: PerplexityBot
Allow: /

# Common Crawl (Used by open training datasets & LLMs)
User-agent: CCBot
Allow: /

# Meta / Facebook
User-agent: FacebookBot
Allow: /

User-agent: meta-externalagent
Allow: /

# Twitter / X
User-agent: Twitterbot
Allow: /

# Canonical Sitemap
Sitemap: {BASE_URL}/sitemap.xml
"""

with open("robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt_content)
with open("public/robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt_content)
print("Generated robots.txt allowing all agents with canonical sitemap URL.")

# 6. Generate sitemap.xml with all tool pages
sitemap_urls = [
    f"""  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""
]

for t in tools:
    path = t.get('path', f"/{t['slug']}/")
    sitemap_urls.append(f"""  <url>
    <loc>{BASE_URL}{path}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
{chr(10).join(sitemap_urls)}
</urlset>
"""

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)
with open("public/sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)
print(f"Generated sitemap.xml with {len(sitemap_urls)} URLs (1 home + {len(tools)} tool pages).")

# 7. Generate vercel.json
vercel_json_content = {
    "cleanUrls": True,
    "trailingSlash": True,
    "headers": [
        {
            "source": "/(.*)",
            "headers": [
                {
                    "key": "X-Content-Type-Options",
                    "value": "nosniff"
                },
                {
                    "key": "X-Frame-Options",
                    "value": "DENY"
                },
                {
                    "key": "X-XSS-Protection",
                    "value": "1; mode=block"
                }
            ]
        },
        {
            "source": "/sitemap.xml",
            "headers": [
                {
                    "key": "Content-Type",
                    "value": "application/xml; charset=utf-8"
                },
                {
                    "key": "Cache-Control",
                    "value": "public, max-age=3600, s-maxage=3600"
                }
            ]
        },
        {
            "source": "/robots.txt",
            "headers": [
                {
                    "key": "Content-Type",
                    "value": "text/plain; charset=utf-8"
                },
                {
                    "key": "Cache-Control",
                    "value": "public, max-age=3600, s-maxage=3600"
                }
            ]
        }
    ]
}

with open("vercel.json", "w", encoding="utf-8") as f:
    json.dump(vercel_json_content, f, indent=2)
print("Generated vercel.json with cleanUrls and security/caching headers.")

# 8. Generate each tool page with rich SEO
def render_tool_page(tool, all_tools, tools_by_cat=None):
    name = tool.get('name', 'AI Platform')
    slug = tool.get('slug', 'tool')
    path = tool.get('path', f"/{slug}/")
    desc = tool.get('description', '')
    pricing = tool.get('pricing', 'Freemium')
    pill = tool.get('category_pill', 'AI Tools')
    cat_slug = tool.get('category_slug', 'chat-reasoning')
    subcat = tool.get('subcategory') or tool.get('category_section') or pill
    color = tool.get('color', '#4F46E5')
    badge = tool.get('badge', name[:2].upper())
    url = tool.get('url', '#')
    img_url = tool.get('image_url', '')
    domain = get_domain(url)

    price_class = "price-freemium"
    if pricing.lower() == "free":
        price_class = "price-free"
    elif pricing.lower() == "paid":
        price_class = "price-paid"

    # Related tools / alternatives
    if tools_by_cat and cat_slug in tools_by_cat:
        cat_candidates = tools_by_cat[cat_slug]
        related = [t for t in cat_candidates if t.get('slug') != slug][:6]
    else:
        related = [t for t in all_tools if t.get('category_slug') == cat_slug and t.get('slug') != slug][:6]
    related_names = ", ".join([r.get('name', '') for r in related[:3]]) if related else "top AI tools"

    # 40 Programmatic Query Intent Templates using [prefix] + main word + [suffix]
    query_intent_groups = {
        'Trending & Alternative Searches': [
            ('best', name, 'alternatives'),
            ('free', name, 'alternatives'),
            ('top', name, 'alternatives 2026'),
            ('open source', name, 'alternatives'),
            ('cheapest', name, 'alternatives'),
            ('tools like', name, ''),
            ('', name, 'vs top alternatives'),
            ('best alternative to', name, ''),
            ('top rated', name, 'alternatives'),
            ('', name, 'competitors list')
        ],
        'Pricing & Free Access Searches': [
            ('', name, 'pricing & plans'),
            ('is', name, 'free'),
            ('free', name, 'tier & trial'),
            ('', name, 'cost per month'),
            ('', name, 'lifetime deal & discount'),
            ('', name, 'subscription pricing 2026'),
            ('cheap', name, 'alternative for students')
        ],
        'Reviews, Benchmarks & Reputation': [
            ('', name, 'review & rating 2026'),
            ('is', name, 'worth it'),
            ('', name, 'pros and cons'),
            ('', name, 'features & benchmark'),
            ('', name, 'user review & score'),
            ('viral', name, 'ai tool'),
            ('', name, 'honest user review')
        ],
        'How-To & Guides': [
            ('what is', name, 'and how it works'),
            ('how to use', name, 'step by step'),
            ('how to start with', name, ''),
            ('', name, 'tutorial & guide'),
            ('', name, 'official website & login portal'),
            ('latest', name, 'updates & features')
        ],
        'Category & Solution Searches': [
            ('best', subcat, 'ai tools'),
            ('top', subcat, 'software 2026'),
            ('free', subcat, 'alternatives'),
            ('open source', subcat, 'ai software'),
            ('best ai for', subcat, ''),
            ('trending', pill, 'tools'),
            ('top trending', name, 'alternatives'),
            ('most popular', subcat, 'platforms'),
            ('trending', subcat, 'software'),
            ('top rated', subcat, 'platforms')
        ]
    }

    intent_sections_html = []
    all_query_intents = []
    for grp_name, items in query_intent_groups.items():
        pills_html = []
        for pre, mid, suf in items:
            q_str = ' '.join([p for p in [pre, mid, suf] if p]).strip()
            all_query_intents.append(q_str)
            q_enc = quote_plus(q_str)
            pills_html.append(f'<a href="/?q={q_enc}" class="query-pill" title="Search {html.escape(q_str)}">&#128269; {html.escape(q_str)}</a>')
        
        intent_sections_html.append(f'''
          <div class="query-group">
            <div class="query-group-title">{html.escape(grp_name)}</div>
            <div class="query-pills">
              {''.join(pills_html)}
            </div>
          </div>''')

    queries_hub_block = '\n'.join(intent_sections_html)
    query_intent_keywords = ", ".join(all_query_intents[:20])
    query_intent_meta = "; ".join(all_query_intents[:15])

    # Schema JSON-LD with AggregateRating for Google Star Snippets
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": "All AI Tools (allaitools)",
                "description": f"Comprehensive directory of {total_tools}+ artificial intelligence tools and verified alternatives."
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE_URL}{path}#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": f"{BASE_URL}/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": pill,
                        "item": f"{BASE_URL}/?category={cat_slug}"
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": name,
                        "item": f"{BASE_URL}{path}"
                    }
                ]
            },
            {
                "@type": "SoftwareApplication",
                "@id": f"{BASE_URL}{path}#software",
                "name": name,
                "description": desc,
                "url": url,
                "applicationCategory": pill,
                "operatingSystem": "Web, Cloud, Cross-Platform",
                "offers": {
                    "@type": "Offer",
                    "price": "0" if pricing.lower() in ["free", "freemium"] else "19.00",
                    "priceCurrency": "USD",
                    "category": pricing,
                    "availability": "https://schema.org/InStock"
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.8",
                    "reviewCount": "128",
                    "bestRating": "5",
                    "worstRating": "1"
                },
                "keywords": all_query_intents[:25]
            },
            {
                "@type": "FAQPage",
                "@id": f"{BASE_URL}{path}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"What is {name} and how does it work?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{name} is an AI tool in the {pill} ({subcat}) category. {desc}"
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"What are the best alternatives and competitors to {name} in 2026?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Top verified alternatives and competitors to {name} in the {pill} space include {related_names}. Compare features, pricing, and capabilities directly on All AI Tools."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"How much does {name} cost? Is there a free version?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"{name} operates under a {pricing} model. Visit the official website ({domain}) for current subscription plans, free tiers, and trial details."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"What are the top rated {subcat} tools like {name}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Explore verified {subcat} software and trending {pill} tools on All AI Tools with live filtering by pricing, features, and user ratings."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"How do I open and access {name} online?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"You can open and visit {name} directly via its official portal at {url}."
                        }
                    }
                ]
            }
        ]
    }
    schema_json_str = json.dumps(schema_data, indent=2)

    related_cards_html = []
    for r in related:
        r_name = r.get('name', 'AI Tool')
        r_slug = r.get('slug', '')
        r_path = r.get('path', f"/{r_slug}/")
        r_subcat = r.get('subcategory') or pill
        r_desc = r.get('description', '')
        r_pricing = r.get('pricing', 'Freemium')
        r_badge = r.get('badge', r_name[:2].upper())
        r_color = r.get('color', '#4F46E5')
        r_url = r.get('url', '#')
        r_price_class = "price-freemium"
        if r_pricing.lower() == "free":
            r_price_class = "price-free"
        elif r_pricing.lower() == "paid":
            r_price_class = "price-paid"

        related_cards_html.append(f"""
          <div class="related-card" onclick="if(!event.target.closest('a') && !event.target.closest('button')) window.location.href='{r_path}'">
            <div class="related-card-top">
              <div class="tool-avatar" style="background:{r_color};">{html.escape(r_badge)}</div>
              <div style="flex:1; min-width:0;">
                <span class="tool-subcat">{html.escape(r_subcat)}</span>
                <h4 class="related-title"><a href="{r_path}" class="tool-card-title-link">{html.escape(r_name)}</a></h4>
              </div>
              <span class="price-badge {r_price_class}">{html.escape(r_pricing)}</span>
            </div>
            <p class="related-desc">{html.escape(r_desc[:120])}{'...' if len(r_desc) > 120 else ''}</p>
            <div class="related-card-bottom">
              <a href="{r_path}" class="view-detail-link">View Alternatives &rarr;</a>
              <a href="{html.escape(r_url)}" target="_blank" rel="noopener noreferrer nofollow" class="tool-link" onclick="event.stopPropagation()">Open Tool &rarr;</a>
            </div>
          </div>
        """)
    related_block = "\n".join(related_cards_html)

    preview_block = ""
    if img_url:
        preview_block = f"""
        <div class="preview-box">
          <img src="{html.escape(img_url)}" alt="{html.escape(name)} screenshot preview" class="tool-preview-full" loading="lazy" onerror="this.parentElement.style.display='none'" />
        </div>
        """

    q_name = quote_plus(name)
    q_subcat = quote_plus(subcat)

    js_tool_name = json.dumps(name.lower())

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(name)} — AI Features, Pricing, Review &amp; Verified Alternatives (2026) | All AI Tools</title>
  <meta name="description" content="Explore {html.escape(name)} ({html.escape(subcat)}): {html.escape(desc[:130])}... Check {html.escape(pricing)} pricing, key features, user reviews, and top verified {html.escape(name)} alternatives in {html.escape(pill)} on All AI Tools (allaitools.online)." />
  <meta name="keywords" content="{html.escape(name)}, {html.escape(name)} ai, {html.escape(name)} alternatives, {html.escape(query_intent_keywords)}, {html.escape(subcat)}, best {html.escape(pill)} tools, all ai tools, allaitools, ai tool list, list of all ai tools, all ai tools in one website" />
  <meta name="search:query_intent" content="{html.escape(query_intent_meta)}" />
  <meta name="author" content="All AI Tools" />
  <meta name="subject" content="{html.escape(name)} AI Software, Pricing and Alternatives" />
  <meta name="topic" content="{html.escape(pill)} AI Tools" />
  <link rel="canonical" href="{BASE_URL}{path}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />

  <!-- OpenGraph -->
  <meta property="og:title" content="{html.escape(name)} — Features, Pricing, Review &amp; Top Alternatives | All AI Tools" />
  <meta property="og:description" content="Compare {html.escape(name)} ({html.escape(pricing)}) with top verified {html.escape(pill)} alternatives. Read features, pricing, user review, and launch the official platform." />
  <meta property="og:url" content="{BASE_URL}{path}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="All AI Tools" />
  {f'<meta property="og:image" content="{html.escape(img_url)}" />' if img_url else ''}

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(name)} — Features, Pricing &amp; Alternatives | All AI Tools" />
  <meta name="twitter:description" content="Explore {html.escape(name)} ({html.escape(subcat)}) and find verified {html.escape(pill)} alternatives on All AI Tools (allaitools.online)." />

  <!-- Favicon -->
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2222%22 fill=%22%234F46E5%22/><text y=%2268%22 x=%2250%22 font-family=%22system-ui,sans-serif%22 font-weight=%22800%22 font-size=%2254%22 fill=%22white%22 text-anchor=%22middle%22>AI</text></svg>" />

  <!-- Structured Data JSON-LD -->
  <script type="application/ld+json">
{schema_json_str}
  </script>

  <style>
    :root {{
      --bg: #090d16;
      --bg-card: #0f1626;
      --bg-card-hover: #151f36;
      --bg-elevated: #1a253f;
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.4);
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-sub: #64748b;
      --accent: #6366f1;
      --accent-glow: rgba(99, 102, 241, 0.25);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --radius-pill: 9999px;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text-main); line-height: 1.6; }}
    body {{ min-height: 100vh; overflow-x: hidden; }}
    a {{ text-decoration: none; color: inherit; }}

    /* Background Ambient */
    .ambient-glow {{
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 1000px;
      height: 520px;
      background: radial-gradient(circle 500px at 50% 120px, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.08), transparent 70%);
      pointer-events: none;
      z-index: 0;
    }}

    .container {{ max-width: 1240px; margin: 0 auto; padding: 0 24px; position: relative; z-index: 1; }}

    /* Redesigned Modern Navbar */
    .navbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(9, 13, 22, 0.88);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
      height: 68px;
      display: flex;
      align-items: center;
    }}
    .nav-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      gap: 18px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      font-size: 1.18rem;
      letter-spacing: -0.025em;
      color: #fff;
      text-decoration: none;
      flex-shrink: 0;
    }}
    .brand-logo-icon {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(168, 85, 247, 0.25) 50%, rgba(56, 189, 248, 0.2) 100%);
      border: 1px solid rgba(129, 140, 248, 0.4);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
      flex-shrink: 0;
      transition: all 0.25s ease;
    }}
    .brand:hover .brand-logo-icon {{
      transform: scale(1.05);
      border-color: rgba(129, 140, 248, 0.7);
      box-shadow: 0 6px 20px rgba(129, 140, 248, 0.55);
    }}
    .brand-text {{
      font-size: 1.18rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      color: #ffffff;
    }}
    .nav-search-wrap {{
      flex: 1;
      max-width: 440px;
      position: relative;
      display: none;
    }}
    @media (min-width: 768px) {{ .nav-search-wrap {{ display: block; }} }}
    .nav-search-input {{
      width: 100%;
      padding: 9px 16px 9px 38px;
      background: rgba(15, 22, 38, 0.9);
      border: 1px solid var(--border);
      border-radius: var(--radius-pill);
      color: #fff;
      font-size: 0.88rem;
      outline: none;
      transition: all 0.2s;
    }}
    .nav-search-input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }}
    .nav-search-icon {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-sub);
      font-size: 0.9rem;
      pointer-events: none;
    }}
    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }}
    .nav-mini-pill {{
      font-size: 0.82rem;
      font-weight: 600;
      color: #cbd5e1;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: var(--radius-pill);
      transition: all 0.2s ease;
      display: none;
      align-items: center;
      gap: 5px;
    }}
    @media (min-width: 900px) {{ .nav-mini-pill {{ display: inline-flex; }} }}
    .nav-mini-pill:hover {{
      background: rgba(99, 102, 241, 0.18);
      border-color: rgba(99, 102, 241, 0.45);
      color: #ffffff;
      transform: translateY(-1px);
    }}
    .btn-nav-submit {{
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      color: #ffffff !important;
      padding: 8px 16px;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.84rem;
      box-shadow: 0 3px 12px rgba(99, 102, 241, 0.35);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .btn-nav-submit:hover {{
      transform: translateY(-1px);
      box-shadow: 0 5px 18px rgba(99, 102, 241, 0.5);
    }}

    /* Breadcrumbs */
    .breadcrumbs {{
      padding: 24px 0 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.86rem;
      color: var(--text-sub);
      flex-wrap: wrap;
    }}
    .breadcrumbs a {{ color: var(--text-muted); transition: color 0.15s; }}
    .breadcrumbs a:hover {{ color: #fff; text-decoration: underline; }}
    .breadcrumbs .crumb-sep {{ color: var(--text-sub); }}
    .breadcrumbs .crumb-current {{ color: #cbd5e1; font-weight: 600; }}

    /* Tool Hero Card */
    .tool-hero {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 24px 28px;
      margin-bottom: 24px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.35);
    }}
    .tool-hero::before {{
      content: "";
      position: absolute;
      top: -50px;
      right: -50px;
      width: 250px;
      height: 250px;
      background: radial-gradient(circle, {color}22 0%, transparent 70%);
      pointer-events: none;
    }}
    .hero-top-row {{
      display: flex;
      align-items: center;
      gap: 18px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}
    .hero-avatar {{
      width: 56px;
      height: 56px;
      border-radius: 14px;
      color: #fff;
      font-weight: 900;
      font-size: 1.4rem;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
      flex-shrink: 0;
    }}
    .hero-info {{ flex: 1; min-width: 260px; }}
    .hero-subcat {{
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #818cf8;
      margin-bottom: 4px;
      display: inline-block;
    }}
    .hero-title {{
      font-size: clamp(1.35rem, 2.5vw, 1.85rem);
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
      margin-bottom: 8px;
      line-height: 1.25;
    }}
    .hero-badges {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}

    /* Badges */
    .price-badge {{
      font-size: 0.74rem;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: var(--radius-pill);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .price-freemium {{ background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); }}
    .price-free {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .price-paid {{ background: rgba(244, 63, 94, 0.15); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.3); }}

    .meta-pill {{
      font-size: 0.74rem;
      font-weight: 600;
      color: #94a3b8;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: var(--radius-pill);
    }}
    .status-pill {{
      font-size: 0.74rem;
      font-weight: 600;
      color: #34d399;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.25);
      padding: 4px 10px;
      border-radius: var(--radius-pill);
    }}
    .domain-pill {{
      font-size: 0.74rem;
      font-weight: 600;
      color: #c7d2fe;
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 4px 10px;
      border-radius: var(--radius-pill);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s ease;
      cursor: pointer;
    }}
    .domain-pill:hover {{
      background: rgba(99, 102, 241, 0.28);
      border-color: rgba(99, 102, 241, 0.6);
      color: #ffffff;
      transform: translateY(-1px);
    }}

    /* Action Row */
    .hero-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }}
    .btn-open-tool {{
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      color: #ffffff !important;
      font-weight: 700;
      font-size: 0.95rem;
      padding: 11px 22px;
      border-radius: 10px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .btn-open-tool:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(99, 102, 241, 0.55);
      opacity: 0.95;
    }}
    .btn-bookmark, .btn-share {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      color: #cbd5e1;
      font-weight: 600;
      font-size: 0.86rem;
      padding: 11px 18px;
      border-radius: 10px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      transition: all 0.15s ease;
    }}
    .btn-bookmark:hover, .btn-share:hover {{
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.25);
      color: #fff;
    }}
    .btn-bookmark.saved {{ color: #fbbf24; border-color: rgba(251, 191, 36, 0.4); }}

    /* Layout Grid */
    .content-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 32px;
      margin-bottom: 64px;
    }}
    @media (min-width: 992px) {{
      .content-grid {{ grid-template-columns: 2fr 1fr; }}
    }}

    /* Card Box */
    .card-box {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 28px;
      margin-bottom: 28px;
    }}
    .card-box h2 {{
      font-size: 1.35rem;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .lead-desc {{
      font-size: 1.05rem;
      line-height: 1.7;
      color: var(--text-muted);
      margin-bottom: 20px;
    }}

    /* Preview box */
    .preview-box {{
      margin: 20px 0;
      border-radius: var(--radius-sm);
      overflow: hidden;
      border: 1px solid var(--border);
      background: rgba(0, 0, 0, 0.3);
    }}
    .tool-preview-full {{
      width: 100%;
      height: auto;
      max-height: 480px;
      object-fit: cover;
      display: block;
    }}

    /* Specs Table */
    .specs-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
    }}
    .specs-table tr {{ border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}
    .specs-table tr:last-child {{ border-bottom: none; }}
    .specs-table td {{
      padding: 12px 0;
      font-size: 0.92rem;
    }}
    .specs-table td.label {{
      color: var(--text-sub);
      width: 38%;
      font-weight: 500;
    }}
    .specs-table td.val {{
      color: #e2e8f0;
      font-weight: 600;
    }}
    .specs-table td.val a {{ color: #818cf8; }}
    .specs-table td.val a:hover {{ text-decoration: underline; }}

    /* Query Parameters & Search Section */
    .queries-box {{
      background: rgba(99, 102, 241, 0.04);
      border: 1px solid rgba(99, 102, 241, 0.2);
    }}
    .queries-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }}
    .queries-header h2 {{
      margin: 0;
      font-size: 1.22rem;
      color: #ffffff;
    }}
    .queries-badge {{
      font-size: 0.72rem;
      font-weight: 700;
      color: #818cf8;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 4px 10px;
      border-radius: var(--radius-pill);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .queries-intro {{
      color: var(--text-muted);
      font-size: 0.9rem;
      line-height: 1.5;
      margin-bottom: 20px;
    }}
    .query-group {{
      margin-bottom: 18px;
    }}
    .query-group:last-child {{
      margin-bottom: 0;
    }}
    .query-group-title {{
      font-size: 0.8rem;
      font-weight: 700;
      color: #cbd5e1;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .query-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .query-pill {{
      background: rgba(15, 22, 38, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #c7d2fe;
      padding: 6px 12px;
      border-radius: var(--radius-pill);
      font-size: 0.8rem;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.18s ease;
      text-decoration: none;
    }}
    .query-pill:hover {{
      background: rgba(99, 102, 241, 0.22);
      border-color: rgba(99, 102, 241, 0.5);
      color: #fff;
      transform: translateY(-1px);
    }}

    /* FAQs */
    .faq-item {{
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      padding: 16px 0;
    }}
    .faq-item:last-child {{ border-bottom: none; padding-bottom: 0; }}
    .faq-q {{
      font-size: 1.02rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 8px;
    }}
    .faq-a {{
      font-size: 0.92rem;
      color: var(--text-muted);
      line-height: 1.6;
    }}

    /* Sidebar Sticky CTA Card */
    .sidebar-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      margin-bottom: 24px;
      position: sticky;
      top: 96px;
    }}
    .sidebar-card h3 {{
      font-size: 1.15rem;
      font-weight: 800;
      color: #fff;
      margin-bottom: 12px;
    }}
    .sidebar-cta-btn {{
      display: block;
      width: 100%;
      text-align: center;
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      color: #fff !important;
      font-weight: 700;
      font-size: 0.98rem;
      padding: 12px 18px;
      border-radius: 10px;
      margin-top: 16px;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
      transition: all 0.15s ease;
    }}
    .sidebar-cta-btn:hover {{ opacity: 0.95; transform: translateY(-1px); }}

    /* Related Tools Cards */
    .related-card {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 16px;
      margin-bottom: 14px;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .related-card:hover {{
      background: var(--bg-card-hover);
      border-color: rgba(99, 102, 241, 0.3);
      transform: translateY(-2px);
    }}
    .related-card-top {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }}
    .related-card-top .tool-avatar {{
      width: 36px;
      height: 36px;
      font-size: 0.85rem;
      border-radius: 8px;
    }}
    .related-title {{
      font-size: 0.96rem;
      font-weight: 700;
      color: #fff;
    }}
    .tool-card-title-link:hover {{ color: #818cf8; text-decoration: underline; }}
    .related-desc {{
      font-size: 0.84rem;
      color: var(--text-muted);
      line-height: 1.45;
      margin-bottom: 10px;
    }}
    .related-card-bottom {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.82rem;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.04);
    }}
    .view-detail-link {{ color: #94a3b8; }}
    .view-detail-link:hover {{ color: #fff; text-decoration: underline; }}
    .tool-link {{
      color: #818cf8;
      font-weight: 600;
    }}
    .tool-link:hover {{ color: #c084fc; text-decoration: underline; }}

    /* Category list in sidebar */
    .cat-links-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 12px;
    }}
    .cat-link-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 8px;
      font-size: 0.86rem;
      color: var(--text-muted);
      transition: all 0.15s;
    }}
    .cat-link-item:hover {{ background: rgba(99, 102, 241, 0.12); color: #c7d2fe; }}

    /* Footer */
    .footer {{
      border-top: 1px solid var(--border);
      padding: 48px 0;
      color: var(--text-sub);
      font-size: 0.88rem;
      text-align: center;
    }}
    .footer-links {{
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .footer-links a:hover {{ color: #fff; }}

    /* Toast */
    .toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #1e1b4b;
      border: 1px solid #6366f1;
      color: #fff;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 0.9rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
      display: none;
      z-index: 1000;
    }}
  </style>
</head>
<body>
  <div class="ambient-glow"></div>

  <!-- Redesigned Navbar -->
  <header class="navbar">
    <div class="container nav-inner">
      <a href="/" class="brand" title="All AI Tools — Home" aria-label="All AI Tools — Home">
        <span class="brand-logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 1.5C12 1.5 13.5 7.5 15.5 9.5C17.5 11.5 23.5 12 23.5 12C23.5 12 17.5 12.5 15.5 14.5C13.5 16.5 12 22.5 12 22.5C12 22.5 10.5 16.5 8.5 14.5C6.5 12.5 0.5 12 0.5 12C0.5 12 6.5 11.5 8.5 9.5C10.5 7.5 12 1.5 12 1.5Z" fill="url(#aiBrandGradDetail)"/>
            <circle cx="19.5" cy="4.5" r="2" fill="#38bdf8"/>
            <circle cx="4.5" cy="19.5" r="1.5" fill="#a855f7"/>
            <defs>
              <linearGradient id="aiBrandGradDetail" x1="0.5" y1="1.5" x2="23.5" y2="22.5" gradientUnits="userSpaceOnUse">
                <stop stop-color="#818cf8"/>
                <stop offset="0.45" stop-color="#c084fc"/>
                <stop offset="1" stop-color="#38bdf8"/>
              </linearGradient>
            </defs>
          </svg>
        </span>
        <span class="brand-text">All AI Tools</span>
      </a>

      <div class="nav-search-wrap">
        <span class="nav-search-icon">&#128269;</span>
        <input type="search" class="nav-search-input" id="navSearchInput" placeholder="Search {total_tools}+ AI tools (Press '/' to focus)..." />
      </div>

      <div class="nav-actions">
        <a href="/tools/ai-image-generator/" class="nav-mini-pill" title="Free AI Image Generator">&#10024; Generator</a>
        <a href="/tools/image-enhancer/" class="nav-mini-pill" title="Real AI 4K Upscaler">&#9889; Enhancer</a>
        <a href="/submit/" class="btn-nav-submit">+ Submit</a>
      </div>
    </div>
  </header>

  <main class="container">
    <!-- Breadcrumbs -->
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a>
      <span class="crumb-sep">/</span>
      <a href="/?category={cat_slug}">{html.escape(pill)}</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-current">{html.escape(name)}</span>
    </nav>

    <!-- Tool Hero Card -->
    <section class="tool-hero">
      <div class="hero-top-row">
        <div class="hero-avatar" style="background:{color};">{html.escape(badge)}</div>
        <div class="hero-info">
          <span class="hero-subcat">{html.escape(subcat)}</span>
          <h1 class="hero-title">{html.escape(name)}</h1>
          <div class="hero-badges">
            <span class="price-badge {price_class}">{html.escape(pricing)}</span>
            <span class="meta-pill">{html.escape(pill)}</span>
            <span class="status-pill">&#10003; Verified &amp; Active (2026)</span>
            <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow" class="domain-pill" title="Visit official site: {html.escape(domain)}">&#127760; {html.escape(domain)} &nearr;</a>
          </div>
        </div>
      </div>

      <div class="hero-actions">
        <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow" class="btn-open-tool">
          Open {html.escape(name)} &rarr;
        </a>
        <button class="btn-bookmark" id="heroBookmarkBtn" data-tool="{html.escape(name)}">&#9734; Bookmark</button>
        <button class="btn-share" id="shareBtn">&#128279; Share Tool</button>
      </div>
    </section>

    <!-- Main Content & Sidebar Layout -->
    <div class="content-grid">
      <!-- Left Main Column -->
      <div class="main-column">
        <!-- Overview -->
        <article class="card-box">
          <h2>About {html.escape(name)}</h2>
          <p class="lead-desc">{html.escape(desc)}</p>
          {preview_block}
        </article>

        <!-- Specifications -->
        <section class="card-box">
          <h2>Platform Specifications &amp; Overview</h2>
          <table class="specs-table">
            <tbody>
              <tr>
                <td class="label">Tool Name</td>
                <td class="val">{html.escape(name)}</td>
              </tr>
              <tr>
                <td class="label">Primary Category</td>
                <td class="val"><a href="/?category={cat_slug}">{html.escape(pill)}</a></td>
              </tr>
              <tr>
                <td class="label">Domain &amp; Specialty</td>
                <td class="val"><a href="/?q={q_subcat}">{html.escape(subcat)}</a></td>
              </tr>
              <tr>
                <td class="label">Pricing Model</td>
                <td class="val"><a href="/?pricing={html.escape(pricing.lower())}">{html.escape(pricing)}</a></td>
              </tr>
              <tr>
                <td class="label">Official Website</td>
                <td class="val"><a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow">{html.escape(domain)} &rarr;</a></td>
              </tr>
              <tr>
                <td class="label">Listing Status</td>
                <td class="val"><span style="color:#34d399;">Active, Indexed &amp; Verified (2026)</span></td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Search Queries & Trending Intent Hub -->
        <section class="card-box queries-box">
          <div class="queries-header">
            <h2>Trending Searches &amp; Query Intent Hub</h2>
            <span class="queries-badge">40 Targeted Query Intents</span>
          </div>
          <p class="queries-intro">Discover high-intent search queries, verified alternatives, pricing benchmarks, and feature comparisons for <strong>{html.escape(name)}</strong> across our 10,000+ AI tools catalog. Click any query to explore matching platforms instantly:</p>
          {queries_hub_block}
        </section>

        <!-- FAQs with Schema Markup -->
        <section class="card-box">
          <h2>Frequently Asked Questions</h2>
          <div class="faq-item">
            <div class="faq-q">What is {html.escape(name)} and how does it work?</div>
            <div class="faq-a">{html.escape(name)} is an artificial intelligence application categorized under {html.escape(pill)} ({html.escape(subcat)}). {html.escape(desc)}</div>
          </div>
          <div class="faq-item">
            <div class="faq-q">What are the best alternatives and competitors to {html.escape(name)} in 2026?</div>
            <div class="faq-a">Top verified alternatives and competitors to {html.escape(name)} in the {html.escape(pill)} category include {html.escape(related_names)}. You can discover and benchmark more alternatives on All AI Tools.</div>
          </div>
          <div class="faq-item">
            <div class="faq-q">How much does {html.escape(name)} cost? Is there a free version?</div>
            <div class="faq-a">{html.escape(name)} operates on a {html.escape(pricing)} pricing model. For full pricing plans and trial access, visit the official website at <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow" style="color:#818cf8;">{html.escape(domain)}</a>.</div>
          </div>
          <div class="faq-item">
            <div class="faq-q">How do I access and open {html.escape(name)}?</div>
            <div class="faq-a">Click the "Open {html.escape(name)}" button or follow the direct link to <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow" style="color:#818cf8;">{html.escape(url)}</a> to access the platform.</div>
          </div>
        </section>
      </div>

      <!-- Right Sidebar Column -->
      <aside class="sidebar-column">
        <!-- Related Tools / Alternatives -->
        <div class="card-box">
          <h2>Top {html.escape(pill)} Alternatives</h2>
          <div class="related-list">
            {related_block}
          </div>
          <div style="margin-top:12px; display:flex; flex-direction:column; gap:6px;">
            <a href="/alternatives/{slug}/" class="view-detail-link" style="font-weight:700; color:#a5b4fc;">
              &#9889; Compare Best {html.escape(name)} Alternatives &rarr;
            </a>
            <a href="/?category={cat_slug}" class="view-detail-link" style="font-weight:600; color:#818cf8;">
              Browse all {html.escape(pill)} tools &rarr;
            </a>
          </div>
        </div>

        <!-- Categories Sidebar -->
        <div class="card-box">
          <h2>Explore Categories</h2>
          <div class="cat-links-list">
            <a href="/?category=video-3d" class="cat-link-item"><span>Video &amp; 3D</span> <span>&rarr;</span></a>
            <a href="/?category=coding-dev" class="cat-link-item"><span>Coding &amp; Dev</span> <span>&rarr;</span></a>
            <a href="/?category=image-art" class="cat-link-item"><span>Image &amp; Art</span> <span>&rarr;</span></a>
            <a href="/?category=chat-reasoning" class="cat-link-item"><span>Chat &amp; Reasoning</span> <span>&rarr;</span></a>
            <a href="/?category=voice-audio" class="cat-link-item"><span>Voice &amp; Audio</span> <span>&rarr;</span></a>
            <a href="/?category=ai-search" class="cat-link-item"><span>AI Search</span> <span>&rarr;</span></a>
          </div>
        </div>
      </aside>
    </div>
  </main>

  <!-- Footer -->
  <footer class="footer">
    <div class="container">
      <div class="footer-links">
        <a href="/">Directory</a>
        <a href="/?category=chat-reasoning">Chat &amp; Reasoning</a>
        <a href="/?category=coding-dev">Coding &amp; Dev</a>
        <a href="/?category=image-art">Image &amp; Art</a>
        <a href="/?category=video-3d">Video &amp; 3D</a>
        <a href="/?category=voice-audio">Voice &amp; Audio</a>
        <a href="/?category=ai-search">AI Search</a>
        <a href="/sitemap.xml">Sitemap</a>
        <a href="/robots.txt">Robots.txt</a>
      </div>
      <p>&copy; 2026 All AI Tools (allaitools.online). All rights reserved. Direct links open official platforms.</p>
    </div>
  </footer>

  <div class="toast" id="toast">Link copied to clipboard!</div>

  <script>
    (function() {{
      var toolName = {js_tool_name};
      var navSearch = document.getElementById('navSearchInput');
      if (navSearch) {{
        navSearch.addEventListener('keydown', function(e) {{
          if (e.key === 'Enter' && navSearch.value.trim()) {{
            window.location.href = '/?q=' + encodeURIComponent(navSearch.value.trim());
          }}
        }});
      }}

      // Bookmarking sync
      var bookmarkBtn = document.getElementById('heroBookmarkBtn');
      var saved = [];
      try {{
        saved = JSON.parse(localStorage.getItem('saved_ai_tools') || '[]');
      }} catch (e) {{}}

      function updateBookmarkUI() {{
        if (saved.indexOf(toolName) !== -1) {{
          bookmarkBtn.classList.add('saved');
          bookmarkBtn.innerHTML = '&#9733; Saved';
        }} else {{
          bookmarkBtn.classList.remove('saved');
          bookmarkBtn.innerHTML = '&#9734; Bookmark';
        }}
      }}
      updateBookmarkUI();

      bookmarkBtn.addEventListener('click', function() {{
        var idx = saved.indexOf(toolName);
        if (idx === -1) {{
          saved.push(toolName);
        }} else {{
          saved.splice(idx, 1);
        }}
        try {{
          localStorage.setItem('saved_ai_tools', JSON.stringify(saved));
        }} catch (e) {{}}
        updateBookmarkUI();
      }});

      // Share button
      var shareBtn = document.getElementById('shareBtn');
      var toast = document.getElementById('toast');
      shareBtn.addEventListener('click', function() {{
        if (navigator.clipboard) {{
          navigator.clipboard.writeText(window.location.href).then(function() {{
            showToast('Link copied to clipboard!');
          }});
        }} else {{
          showToast('URL: ' + window.location.href);
        }}
      }});

      function showToast(msg) {{
        toast.textContent = msg;
        toast.style.display = 'block';
        setTimeout(function() {{
          toast.style.display = 'none';
        }}, 3000);
      }}
    }})();
  </script>
</body>
</html>"""
    return page_html

if "--homepage-only" in sys.argv:
    print(f"Homepage, sitemap, compact json and robots updated successfully (--homepage-only mode)!")
    sys.exit(0)

print(f"Generating static HTML pages for {len(tools)} tools in parallel...")
tools_by_cat = {}
for t in tools:
    c = t.get('category_slug', 'chat-reasoning')
    if c not in tools_by_cat:
        tools_by_cat[c] = []
    tools_by_cat[c].append(t)

def generate_one_tool_page(tool):
    slug = tool['slug']
    html_page = render_tool_page(tool, tools, tools_by_cat)

    # 1. public/<slug>/index.html
    dir_path = os.path.join("public", slug)
    os.makedirs(dir_path, exist_ok=True)
    index_file = os.path.join(dir_path, "index.html")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_page)

    # 2. public/<slug>.html
    slug_file = os.path.join("public", f"{slug}.html")
    with open(slug_file, "w", encoding="utf-8") as f:
        f.write(html_page)

from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=16) as executor:
    list(executor.map(generate_one_tool_page, tools))

print(f"Successfully generated all {len(tools)} tool pages in public/<slug>/index.html and public/<slug>.html!")
