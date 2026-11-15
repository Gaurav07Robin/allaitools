import os
import xml.etree.ElementTree as ET

urls_to_check = [
    "https://www.allaitools.online/tools/ai-image-generator/",
    "https://www.allaitools.online/tools/image-enhancer/"
]

sitemap_files = ["sitemap.xml", "public/sitemap.xml", "dist/sitemap.xml"]

for sm in sitemap_files:
    if not os.path.exists(sm):
        print(f"{sm} does not exist!")
        continue
    print(f"=== {sm} ===")
    tree = ET.parse(sm)
    root = tree.getroot()
    entries = {}
    for u in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        loc = u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if loc is not None and loc.text:
            loc_text = loc.text.strip()
            entries[loc_text] = {
                "priority": getattr(u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}priority"), "text", None),
                "changefreq": getattr(u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq"), "text", None),
                "lastmod": getattr(u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod"), "text", None)
            }
    for target in urls_to_check:
        if target in entries:
            e = entries[target]
            print(f"  [FOUND & VALIDATED] {target}")
            print(f"    priority: {e['priority']}, changefreq: {e['changefreq']}, lastmod: {e['lastmod']}")
        else:
            print(f"  [MISSING] {target}")

print("\n=== Checking disk files in public/ ===")
for path in [
    "public/tools/ai-image-generator/index.html",
    "public/tools/ai-image-generator.html",
    "public/tools/image-enhancer/index.html",
    "public/tools/image-enhancer.html"
]:
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"  {path}: exists={exists}, size={size} bytes")
