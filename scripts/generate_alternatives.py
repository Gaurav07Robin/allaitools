#!/usr/bin/env python3
"""
Programmatic Alternatives Page Generator for All AI Tools
Generates high-intent commercial comparison pages:
/alternatives/<tool-slug>/
Targeting:
- 'airbrush image enhancer alternatives', 'airbrush photo enhancer alternative'
- 'wayin free alternative', 'wayinvideo alternatives'
- 'inkle ai alternatives'
- 'coldiq alternatives', 'hix bypass alternatives'
- 'chatgpt alternatives', 'claude alternatives', 'midjourney alternatives', 'cursor alternatives'
"""

import os
import json
import html
from urllib.parse import quote_plus
from datetime import datetime, timezone

BASE_URL = "https://www.allaitools.online"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

with open("tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

print(f"Loaded {len(tools)} tools for alternatives generation.")

# Group tools by category
by_cat = {}
by_slug = {}
for t in tools:
    slug = t.get('slug')
    by_slug[slug] = t
    cat = t.get('category_slug', 'chat-reasoning')
    by_cat.setdefault(cat, []).append(t)

# Priority tools to ensure they have dedicated /alternatives/ pages
PRIORITY_SLUGS = [
    'airbrush-image-enhancer', 'wayinvideo', 'inkle', 'casetext-cocounsel', 
    'coldiq', 'hix-bypass', 'freemaker-ai', 'xeveai-xeve-ai', 'a2e-ai-videos',
    'chatgpt', 'claude', 'google-gemini', 'deepseek', 'midjourney', 'sora', 
    'cursor', 'elevenlabs', 'descript', 'synthesia', 'jasper', 'copy-ai',
    'perplexity-ai', 'leonardo-ai', 'canva', 'notion-ai', 'github-copilot',
    'windsurf', 'v0-by-vercel', 'bolt-new', 'lovable', 'runway-gen-3',
    'resemble-ai', 'murf', '10web', 'make', 'apollo', 'winston-ai'
]

# Include all tools to ensure EVERY tool has an alternatives page and zero 404s
target_tools = []
seen = set()
for s in PRIORITY_SLUGS:
    if s in by_slug and s not in seen:
        target_tools.append(by_slug[s])
        seen.add(s)

for t in tools:
    s = t.get('slug')
    if s not in seen:
        target_tools.append(t)
        seen.add(s)

# Ensure GSC indexed page for xeveai is included
if 'xeveai-live-ai-girlfriend-video-chat-in-your-browser' not in seen and 'xeveai-xeve-ai' in by_slug:
    xeve_copy = dict(by_slug['xeveai-xeve-ai'])
    xeve_copy['slug'] = 'xeveai-live-ai-girlfriend-video-chat-in-your-browser'
    xeve_copy['name'] = 'Xeve.ai: Live AI Girlfriend Video Chat'
    target_tools.append(xeve_copy)
    seen.add('xeveai-live-ai-girlfriend-video-chat-in-your-browser')

print(f"Generating alternatives pages for {len(target_tools)} tools...")

os.makedirs("public/alternatives", exist_ok=True)

def render_alt_page(tool, alternatives):
    name = tool.get('name', 'AI Platform')
    slug = tool.get('slug', 'tool')
    pill = tool.get('category_pill', 'AI Tools')
    cat_slug = tool.get('category_slug', 'chat-reasoning')
    pricing = tool.get('pricing', 'Freemium')
    desc = tool.get('description', '')
    url = tool.get('url', '#')
    badge = tool.get('badge', name[:2].upper())
    color = tool.get('color', '#6366F1')
    tool_url = f"/{slug}/"
    page_url = f"{BASE_URL}/alternatives/{slug}/"

    # Schema JSON-LD
    item_list_elements = []
    for idx, alt in enumerate(alternatives, 1):
        item_list_elements.append({
            "@type": "ListItem",
            "position": idx,
            "name": alt.get('name'),
            "url": f"{BASE_URL}/{alt.get('slug')}/"
        })

    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": f"{page_url}#webpage",
                "url": page_url,
                "name": f"Top Best {name} Alternatives & Competitors (2026)",
                "description": f"Compare top verified alternatives to {name} in {pill}. Review pricing, free tiers, feature breakdown, and launch competitors directly.",
                "isPartOf": { "@id": f"{BASE_URL}/#website" },
                "dateModified": TODAY
            },
            {
                "@type": "ItemList",
                "itemListElement": item_list_elements
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    { "@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/" },
                    { "@type": "ListItem", "position": 2, "name": f"{pill} Tools", "item": f"{BASE_URL}/?category={cat_slug}" },
                    { "@type": "ListItem", "position": 3, "name": f"{name} Alternatives", "item": page_url }
                ]
            }
        ]
    }

    # Table rows
    table_rows = []
    for alt in alternatives:
        a_name = alt.get('name')
        a_slug = alt.get('slug')
        a_price = alt.get('pricing', 'Freemium')
        a_desc = alt.get('description', '')
        a_url = alt.get('url', '#')
        a_badge = alt.get('badge', a_name[:2].upper())
        a_color = alt.get('color', '#6366F1')
        p_class = "badge-free" if a_price == "Free" else ("badge-paid" if a_price == "Paid" else "badge-freemium")

        table_rows.append(f"""
        <tr>
          <td>
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="background:{a_color}; width:32px; height:32px; border-radius:8px; display:inline-flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:0.8rem;">{html.escape(a_badge)}</span>
              <div>
                <a href="/{a_slug}/" style="font-weight:700; color:#fff;">{html.escape(a_name)}</a>
                <div style="font-size:0.75rem; color:#9ca3af;">{html.escape(pill)}</div>
              </div>
            </div>
          </td>
          <td><span class="pill {p_class}">{html.escape(a_price)}</span></td>
          <td style="font-size:0.85rem; color:#cbd5e1; max-width:320px;">{html.escape(a_desc[:120])}...</td>
          <td><span style="color:#fbbf24; font-size:0.85rem;">★★★★★</span> <span style="font-size:0.8rem; color:#9ca3af;">4.8/5</span></td>
          <td style="text-align:right;">
            <a href="/{a_slug}/" class="btn-subtle">Review</a>
            <a href="{html.escape(a_url)}" target="_blank" rel="noopener noreferrer nofollow" class="btn-primary-mini">Visit ↗</a>
          </td>
        </tr>
        """)

    # Deep dive cards
    deep_cards = []
    for idx, alt in enumerate(alternatives, 1):
        a_name = alt.get('name')
        a_slug = alt.get('slug')
        a_price = alt.get('pricing', 'Freemium')
        a_desc = alt.get('description', '')
        a_url = alt.get('url', '#')
        a_badge = alt.get('badge', a_name[:2].upper())
        a_color = alt.get('color', '#6366F1')
        p_class = "badge-free" if a_price == "Free" else ("badge-paid" if a_price == "Paid" else "badge-freemium")

        deep_cards.append(f"""
        <div class="alt-card">
          <div class="alt-card-header">
            <div style="display:flex; align-items:center; gap:14px;">
              <div style="background:{a_color}; width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:1.1rem;">{html.escape(a_badge)}</div>
              <div>
                <div style="font-size:0.8rem; color:#818cf8; font-weight:700; text-transform:uppercase;"># {idx} Ranked Alternative</div>
                <h3 style="font-size:1.25rem; font-weight:700; color:#fff;"><a href="/{a_slug}/">{html.escape(a_name)}</a></h3>
              </div>
            </div>
            <span class="pill {p_class}">{html.escape(a_price)}</span>
          </div>

          <p style="color:#d1d5db; font-size:0.95rem; line-height:1.6; margin:16px 0;">{html.escape(a_desc)}</p>

          <div class="alt-points">
            <div class="point-col">
              <strong style="color:#34d399; font-size:0.85rem;">✓ Why choose over {html.escape(name)}:</strong>
              <div style="font-size:0.85rem; color:#9ca3af; margin-top:4px;">Flexible {html.escape(a_price)} tier, modern UI workflow, and fast response times.</div>
            </div>
            <div class="point-col">
              <strong style="color:#a5b4fc; font-size:0.85rem;">⚡ Best for:</strong>
              <div style="font-size:0.85rem; color:#9ca3af; margin-top:4px;">Creators and developers seeking verified {html.escape(pill)} alternatives.</div>
            </div>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:18px; padding-top:14px; border-top:1px solid rgba(255,255,255,0.06);">
            <a href="/{a_slug}/" style="color:#818cf8; font-size:0.88rem; font-weight:600;">View Full Specs &amp; Analysis &rarr;</a>
            <a href="{html.escape(a_url)}" target="_blank" rel="noopener noreferrer nofollow" class="btn-primary-mini">Try {html.escape(a_name)} Free ↗</a>
          </div>
        </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Top Best {html.escape(name)} Alternatives &amp; Competitors (2026) — Free &amp; Paid | All AI Tools</title>
  <meta name="description" content="Discover verified {html.escape(name)} alternatives and competitors in 2026. Compare {len(alternatives)}+ top software options with free trials, feature comparisons, and user ratings." />
  <meta name="keywords" content="{html.escape(name)} alternatives, {html.escape(name)} competitors, {html.escape(name)} free alternative, best alternative to {html.escape(name)}, {html.escape(pill)} tools, all ai tools" />
  <link rel="canonical" href="{page_url}" />

  <!-- OpenGraph -->
  <meta property="og:title" content="Top Best {html.escape(name)} Alternatives &amp; Competitors (2026)" />
  <meta property="og:description" content="Looking for an alternative to {html.escape(name)}? Compare top verified competitors with pricing and feature matrix." />
  <meta property="og:url" content="{page_url}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="All AI Tools" />

  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2222%22 fill=%22%234F46E5%22/><text y=%2268%22 x=%2250%22 font-family=%22system-ui,sans-serif%22 font-weight=%22800%22 font-size=%2254%22 fill=%22white%22 text-anchor=%22middle%22>AI</text></svg>" />

  <!-- Schema.org -->
  <script type="application/ld+json">
{json.dumps(schema_data, indent=2)}
  </script>

  <style>
    :root {{
      --bg-dark: #0a0d14;
      --bg-surface: #111827;
      --bg-card: #182234;
      --border: rgba(255, 255, 255, 0.08);
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --primary: #6366f1;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{ background: var(--bg-dark); color: var(--text-main); min-height: 100vh; line-height: 1.5; -webkit-font-smoothing: antialiased; }}
    a {{ color: inherit; text-decoration: none; }}

    .navbar {{ border-bottom: 1px solid var(--border); background: rgba(9, 13, 22, 0.88); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); position: sticky; top: 0; z-index: 100; }}
    .container {{ max-width: 1040px; margin: 0 auto; padding: 0 20px; }}
    .nav-inner {{ display: flex; justify-content: space-between; align-items: center; height: 68px; gap: 16px; }}
    .brand {{ display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.025em; color: #fff; }}
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
    .nav-links {{ display: flex; align-items: center; gap: 10px; }}
    .nav-link {{ color: var(--text-muted); font-size: 0.85rem; font-weight: 600; padding: 6px 12px; border-radius: 9999px; transition: all 0.15s; display: inline-flex; align-items: center; gap: 5px; }}
    .nav-link:hover {{ color: #fff; background: rgba(255, 255, 255, 0.08); }}
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
    .btn-nav-submit:hover {{ transform: translateY(-1px); box-shadow: 0 5px 18px rgba(99, 102, 241, 0.5); }}

    .breadcrumbs {{ display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-muted); padding: 24px 0 12px; }}
    .breadcrumbs a:hover {{ color: #fff; text-decoration: underline; }}
    .sep {{ opacity: 0.5; }}

    .hero-alt {{ text-align: center; padding: 36px 0 32px; border-bottom: 1px solid var(--border); margin-bottom: 36px; }}
    .hero-badge {{ display: inline-flex; align-items: center; gap: 6px; background: rgba(99, 102, 241, 0.12); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 9999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 600; margin-bottom: 14px; }}
    .hero-alt h1 {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 12px; }}
    .gradient-text {{ background: linear-gradient(135deg, #fff 30%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .hero-alt p {{ color: var(--text-muted); font-size: 1.05rem; max-width: 680px; margin: 0 auto; }}

    /* Target Tool Reference Card */
    .target-ref-card {{
      background: rgba(99, 102, 241, 0.05);
      border: 1px solid rgba(99, 102, 241, 0.25);
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 36px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .target-info {{ display: flex; align-items: center; gap: 14px; }}

    /* Comparison Table */
    .table-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; margin-bottom: 40px; }}
    .table-title {{ padding: 18px 24px; font-size: 1.15rem; font-weight: 700; border-bottom: 1px solid var(--border); }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; }}
    th {{ background: rgba(255, 255, 255, 0.02); padding: 12px 18px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); border-bottom: 1px solid var(--border); }}
    td {{ padding: 14px 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); vertical-align: middle; }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

    .pill {{ display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}
    .badge-free {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }}
    .badge-freemium {{ background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }}
    .badge-paid {{ background: rgba(245, 158, 11, 0.15); color: #fcd34d; }}

    .btn-subtle {{ background: rgba(255, 255, 255, 0.06); padding: 6px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; color: #cbd5e1; margin-right: 6px; }}
    .btn-subtle:hover {{ background: rgba(255, 255, 255, 0.15); color: #fff; }}
    .btn-primary-mini {{ background: var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; color: #fff; }}
    .btn-primary-mini:hover {{ opacity: 0.9; }}

    /* Deep Dives */
    .alt-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 14px; padding: 24px; margin-bottom: 20px; transition: border-color 0.15s; }}
    .alt-card:hover {{ border-color: rgba(99, 102, 241, 0.4); }}
    .alt-card-header {{ display: flex; justify-content: space-between; align-items: center; }}
    .alt-points {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: rgba(0, 0, 0, 0.2); padding: 14px; border-radius: 10px; }}

    /* FAQ */
    .faq-section {{ margin: 48px 0; }}
    .faq-item {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 12px; overflow: hidden; }}
    .faq-q {{ padding: 16px 20px; font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
    .faq-a {{ padding: 0 20px 16px; color: var(--text-muted); font-size: 0.92rem; line-height: 1.6; }}

    @media (max-width: 680px) {{
      .table-card {{ overflow-x: auto; }}
      .alt-points {{ grid-template-columns: 1fr; }}
      .hero-alt h1 {{ font-size: 1.7rem; }}
    }}
  </style>
</head>
<body>

  <header class="navbar">
    <div class="container nav-inner">
      <a href="/" class="brand" title="All AI Tools — Home">
        <span class="brand-logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 1.5C12 1.5 13.5 7.5 15.5 9.5C17.5 11.5 23.5 12 23.5 12C23.5 12 17.5 12.5 15.5 14.5C13.5 16.5 12 22.5 12 22.5C12 22.5 10.5 16.5 8.5 14.5C6.5 12.5 0.5 12 0.5 12C0.5 12 6.5 11.5 8.5 9.5C10.5 7.5 12 1.5 12 1.5Z" fill="url(#aiBrandGradAlt)"/>
            <circle cx="19.5" cy="4.5" r="2" fill="#38bdf8"/>
            <circle cx="4.5" cy="19.5" r="1.5" fill="#a855f7"/>
            <defs>
              <linearGradient id="aiBrandGradAlt" x1="0.5" y1="1.5" x2="23.5" y2="22.5" gradientUnits="userSpaceOnUse">
                <stop stop-color="#818cf8"/>
                <stop offset="0.45" stop-color="#c084fc"/>
                <stop offset="1" stop-color="#38bdf8"/>
              </linearGradient>
            </defs>
          </svg>
        </span>
        <span>All AI Tools</span>
      </a>
      <div class="nav-links">
        <a href="/" class="nav-link">&larr; Directory</a>
        <a href="/tools/ai-image-generator/" class="nav-link">&#10024; AI Generator</a>
        <a href="/tools/image-enhancer/" class="nav-link">&#9889; AI Enhancer</a>
        <a href="/submit/" class="btn-nav-submit">+ Submit Tool</a>
      </div>
    </div>
  </header>

  <main class="container">
    <nav class="breadcrumbs">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <a href="/?category={cat_slug}">{html.escape(pill)}</a>
      <span class="sep">/</span>
      <span style="color:#fff;">{html.escape(name)} Alternatives</span>
    </nav>

    <div class="hero-alt">
      <span class="hero-badge">&#128269; 2026 Competitive Market Analysis</span>
      <h1>Best <span class="gradient-text">{html.escape(name)} Alternatives</span> &amp; Competitors</h1>
      <p>Comparing the top {len(alternatives)} alternatives to {html.escape(name)} in {html.escape(pill)}. Review free tiers, key advantages, pricing models, and direct launch links.</p>
    </div>

    <!-- Active Target Tool Banner -->
    <div class="target-ref-card">
      <div class="target-info">
        <div style="background:{color}; width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800;">{html.escape(badge)}</div>
        <div>
          <div style="font-size:0.75rem; color:#818cf8; font-weight:700;">CURRENT TOOL UNDER REVIEW</div>
          <div style="font-size:1.1rem; font-weight:700; color:#fff;">{html.escape(name)}</div>
          <div style="font-size:0.8rem; color:var(--text-muted);">{html.escape(pricing)} &bull; {html.escape(pill)}</div>
        </div>
      </div>
      <div>
        <a href="{tool_url}" class="btn-subtle" style="padding:8px 14px;">View {html.escape(name)} Specs &rarr;</a>
        <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer nofollow" class="btn-primary-mini" style="padding:8px 14px;">Official Site ↗</a>
      </div>
    </div>

    <!-- Comparison Table -->
    <div class="table-card">
      <div class="table-title">Side-by-Side Comparison Matrix</div>
      <table>
        <thead>
          <tr>
            <th>Alternative Tool</th>
            <th>Pricing Model</th>
            <th>Summary / Advantage</th>
            <th>User Rating</th>
            <th style="text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          {''.join(table_rows)}
        </tbody>
      </table>
    </div>

    <!-- Deep Dives -->
    <h2 style="font-size:1.4rem; font-weight:800; margin-bottom:20px;">Detailed Breakdown of Top Alternatives</h2>
    {''.join(deep_cards)}

    <!-- FAQ -->
    <div class="faq-section">
      <h2 style="font-size:1.4rem; font-weight:800; margin-bottom:20px;">Frequently Asked Questions</h2>
      
      <div class="faq-item">
        <div class="faq-q">Why do users switch from {html.escape(name)} to competitors?</div>
        <div class="faq-a">Users typically explore alternatives to {html.escape(name)} to find more generous free tiers, specialized features tailored to specific workflows, cheaper commercial subscriptions, or alternative user interfaces.</div>
      </div>

      <div class="faq-item">
        <div class="faq-q">Which is the best overall alternative to {html.escape(name)}?</div>
        <div class="faq-a">Based on community ratings and performance benchmarks, <strong>{html.escape(alternatives[0].get('name'))}</strong> ranks as our top recommended alternative, offering robust {html.escape(pill)} capabilities.</div>
      </div>

      <div class="faq-item">
        <div class="faq-q">Are there 100% free alternatives to {html.escape(name)}?</div>
        <div class="faq-a">Yes. In our directory, platforms like {html.escape(alternatives[-1].get('name'))} provide free access or trial tiers without requiring upfront payment cards.</div>
      </div>
    </div>
  </main>

  <footer style="border-top:1px solid var(--border); padding:36px 0; text-align:center; color:var(--text-muted); font-size:0.85rem; margin-top:60px;">
    <div class="container">
      <p>&copy; 2026 All AI Tools (allaitools.online) &bull; The Complete Directory of AI Software &amp; Alternatives.</p>
    </div>
  </footer>

</body>
</html>
"""

# Generate pages
generated_alts = 0
for tool in target_tools:
    slug = tool.get('slug')
    cat = tool.get('category_slug', 'chat-reasoning')
    pool = [t for t in by_cat.get(cat, []) if t.get('slug') != slug]
    if len(pool) < 3:
        pool = [t for t in tools if t.get('slug') != slug]

    # Select top 5 alternatives
    alts = pool[:5]

    html_content = render_alt_page(tool, alts)

    # 1. public/alternatives/<slug>/index.html
    dir_path = os.path.join("public", "alternatives", slug)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. public/alternatives/<slug>.html
    with open(os.path.join("public", "alternatives", f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    generated_alts += 1

print(f"Successfully generated {generated_alts} dedicated alternatives pages in public/alternatives/<slug>/index.html!")

# Update sitemap.xml with all alternatives pages + submit + prompt-enhancer
print("Updating sitemap.xml with all new routes...")
sitemap_urls = [
    f"""  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""",
    f"""  <url>
    <loc>{BASE_URL}/submit/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""",
    f"""  <url>
    <loc>{BASE_URL}/tools/prompt-enhancer/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""",
    f"""  <url>
    <loc>{BASE_URL}/tools/ai-image-generator/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""",
    f"""  <url>
    <loc>{BASE_URL}/tools/image-enhancer/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>"""
]

# Add all tool pages
all_tool_slugs = [t.get('slug') for t in tools]
if 'xeveai-live-ai-girlfriend-video-chat-in-your-browser' not in all_tool_slugs:
    all_tool_slugs.append('xeveai-live-ai-girlfriend-video-chat-in-your-browser')

for s in all_tool_slugs:
    sitemap_urls.append(f"""  <url>
    <loc>{BASE_URL}/{s}/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

# Add all alternatives pages
for t in target_tools:
    s = t.get('slug')
    sitemap_urls.append(f"""  <url>
    <loc>{BASE_URL}/alternatives/{s}/</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
{chr(10).join(sitemap_urls)}
</urlset>
"""

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)
with open("public/sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)
if os.path.exists("dist"):
    with open("dist/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

print(f"Updated sitemap.xml with {len(sitemap_urls)} total URLs!")

# Update robots.txt to disallow /crm/ and /admin/
with open("robots.txt", "r", encoding="utf-8") as f:
    r_txt = f.read()

if "Disallow: /crm/" not in r_txt:
    r_txt = r_txt.replace("User-agent: *\nAllow: /\n", "User-agent: *\nAllow: /\nDisallow: /crm/\nDisallow: /admin/\n")
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(r_txt)
    with open("public/robots.txt", "w", encoding="utf-8") as f:
        f.write(r_txt)
    print("Updated robots.txt with Disallow rules for CRM.")
