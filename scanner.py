#!/usr/bin/env python3
"""
Daily ESG compliance scanner for Balaji Amines.

Runs on GitHub Actions once a day. It:
  1. Reads data.json (the dashboard's data file).
  2. Scans recent SEBI / ESG / BRSR / LODR news (free Google News RSS — no API key).
  3. Logs every genuinely new item to the "feed" (the daily change log).
  4. NEVER removes an existing obligation. Relevant obligations stay pinned forever.
       - If an item matches an existing obligation  -> it ANNOTATES that card
         (adds an "UPDATED" flag + note + source link). The card stays in place.
       - If an item is a clearly new SEBI requirement -> it ADDS a new card
         (marked "NEW", flagged for you to confirm the details).
  5. Writes data.json back. GitHub Actions commits the change and the site refreshes.

Safe by design: obligations are only added or annotated, never deleted.
"""

import json, re, hashlib, sys, os
from datetime import datetime, timezone
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# ---- Searches (free Google News RSS). "when:2d" = last 2 days, with overlap so nothing is missed.
QUERIES = [
    "SEBI ESG disclosure BRSR when:2d",
    "SEBI BRSR Core assurance when:2d",
    "SEBI LODR ESG amendment when:2d",
    "SEBI ESG rating provider when:2d",
    "SEBI ESG mutual fund scheme when:2d",
]

# ---- An item must mention at least one of these to be considered ESG-compliance relevant.
RELEVANCE = ["esg", "brsr", "business responsibility", "sustainability report",
             "lodr", "listing obligations", "esg rating", "greenwashing",
             "value chain", "scope 3", "sustainability disclosure", "brsr core"]

# ---- Words that signal an actual new/changed rule (not just commentary).
REG_TRIGGERS = ["circular", "notif", "mandate", "mandat", "introduc", "amend", "revis",
                "norms", "framework", "requirement", "rule", "deadline", "extend",
                "timeline", "prescrib", "relax", "guideline", "master direction"]

# ---- Which regulated stream an item belongs to.
STREAM_KEYS = {
    "Listed Company": ["brsr", "lodr", "listing", "annual report", "value chain",
                       "disclosure", "listed compan", "listed entit"],
    "ERP":            ["rating provider", "erp", "esg rating", "credit rating agenc"],
    "Mutual Fund":    ["mutual fund", "amc", "scheme", "aum", "stewardship",
                       "portfolio", "fund manager"],
}

MAX_FEED = 80          # keep the change log this long
MAX_NEW_PER_RUN = 3    # safety cap on auto-added obligation cards per day
UA = "Mozilla/5.0 (compatible; ESG-Compliance-Scanner/1.0)"


def log(m): print(f"[scanner] {m}")


def item_id(link, title):
    return hashlib.sha1((link or title).encode("utf-8")).hexdigest()[:16]


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").replace("&nbsp;", " ").strip()


def classify_type(text):
    t = text.lower()
    if any(w in t for w in ["repeal", "withdraw", "rescind", "omit", "scrap"]):
        return "rem"
    if any(w in t for w in ["deadline", "last date", "extend", "timeline", "due date", "cut-off"]):
        return "dl"
    if any(w in t for w in ["amend", "revis", "modif", "update", "relax", "tighten", "norms"]):
        return "upd"
    return "add"


def classify_stream(text):
    t = text.lower()
    best, best_n = "All", 0
    for stream, keys in STREAM_KEYS.items():
        n = sum(1 for k in keys if k in t)
        if n > best_n:
            best, best_n = stream, n
    return best


def match_obligation(text, obligations):
    """Return the best-matching existing obligation id, or None."""
    t = text.lower()
    best, best_n = None, 0
    for o in obligations:
        n = sum(1 for k in o.get("keywords", []) if k in t)
        if n > best_n:
            best, best_n = o, n
    return best if best_n >= 1 else None


def fetch_rss(query):
    url = ("https://news.google.com/rss/search?q=" + quote_plus(query)
           + "&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=25) as r:
            raw = r.read().decode("utf-8", "ignore")
    except Exception as e:
        log(f"fetch failed for '{query}': {e}")
        return []
    items = []
    for block in re.findall(r"<item>(.*?)</item>", raw, re.S):
        def grab(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
            return strip_html(re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1))) if m else ""
        title = grab("title")
        link = grab("link")
        desc = grab("description")
        pub = grab("pubDate")
        src_m = re.search(r'<source[^>]*>(.*?)</source>', block, re.S)
        source = strip_html(src_m.group(1)) if src_m else "News"
        if title and link:
            items.append({"title": title, "link": link, "desc": desc,
                          "pub": pub, "source": source})
    return items


def pub_to_when(pub):
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(pub, fmt).strftime("%d %b %Y")
        except Exception:
            pass
    return datetime.now(timezone.utc).strftime("%d %b %Y")


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    obligations = data.setdefault("obligations", [])
    feed = data.setdefault("feed", [])
    seen = set(data.setdefault("seen", []))

    # gather + dedupe candidates
    candidates = {}
    for q in QUERIES:
        for it in fetch_rss(q):
            iid = item_id(it["link"], it["title"])
            if iid in seen or iid in candidates:
                continue
            blob = (it["title"] + " " + it["desc"]).lower()
            if not any(k in blob for k in RELEVANCE):
                continue
            candidates[iid] = it
    log(f"{len(candidates)} new relevant item(s) found")

    new_feed, annotated, added = [], 0, 0
    for iid, it in candidates.items():
        seen.add(iid)
        blob = it["title"] + " " + it["desc"]
        ftype = classify_type(blob)
        stream = classify_stream(blob)
        when = pub_to_when(it["pub"])
        desc = (it["desc"][:240] + "…") if len(it["desc"]) > 240 else (it["desc"] or it["title"])

        match = match_obligation(blob, obligations)
        if match:
            # annotate the existing obligation — never remove it
            match["lastUpdate"] = {"on": when,
                                   "note": f"Flagged by daily scan: “{it['title']}”. Review the source and update the details if confirmed.",
                                   "url": it["link"]}
            ftype = "upd" if ftype == "add" else ftype
            annotated += 1
        elif (any(w in blob.lower() for w in REG_TRIGGERS)
              and "sebi" in blob.lower()
              and added < MAX_NEW_PER_RUN):
            # looks like a brand-new SEBI requirement with no existing match -> add a card to review
            obligations.append({
                "id": "auto-" + iid,
                "stream": stream if stream != "All" else "Listed Company",
                "rel": stream in ("Listed Company", "All"),
                "pinned": False, "isNew": True, "addedOn": when,
                "area": "New / detected",
                "title": it["title"][:140],
                "desc": "Auto-detected from SEBI/ESG news — confirm the exact requirement, applicability and dates against the source circular before acting.",
                "apply": "To be confirmed", "basis": "To be confirmed",
                "eff": "To be confirmed", "status": "up",
                "src": it["source"], "para": "—",
                "keywords": [], "url": it["link"],
            })
            added += 1

        new_feed.append({"when": when, "type": ftype, "title": it["title"][:160],
                         "desc": desc, "src": it["source"], "url": it["link"],
                         "stream": stream})

    # newest first; keep pinned baseline entries; trim
    data["feed"] = (new_feed + feed)[:MAX_FEED]
    data["seen"] = list(seen)[-4000:]
    data["lastSync"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"done — {len(new_feed)} new feed item(s), {annotated} obligation(s) annotated, "
        f"{added} new obligation(s) added. Total obligations: {len(obligations)} (none removed).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(0)  # never fail the workflow — a bad scan day shouldn't break the site
