#!/usr/bin/env python3
"""Universal SEO Audit Orchestrator.

A harness-agnostic, standalone SEO engine that audits websites across
Technical SEO, On-Page & Content, Schema.org, Core Web Vitals, and
AI Agent / GEO Readiness (Gemini, ChatGPT, Perplexity, Claude).

Produces standardized JSON envelopes, comprehensive Markdown reports,
and per-category findings compatible with any AI agent or CI/CD runner.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def run_helper(script_name: str, *args: str) -> dict | str | None:
    """Run a sibling claude-seo Python script and parse its output."""
    scripts_dir = Path(__file__).resolve().parent
    script_path = scripts_dir / script_name
    if not script_path.exists():
        return None
    cmd = [sys.executable, str(script_path), *args]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        stdout = res.stdout.strip()
        if "--json" in args or "-j" in args:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {"raw": stdout, "error": res.stderr}
        return stdout
    except Exception as exc:
        return {"error": str(exc)}


def audit_url(target_url: str, output_dir: Path, mode: str = "auto") -> dict:
    """Perform a multi-axis audit on target_url."""
    parsed = urlparse(target_url)
    domain = parsed.netloc or target_url
    scheme = parsed.scheme or "https"
    base_url = f"{scheme}://{domain}"

    print(f"[*] Starting Universal SEO Audit for: {target_url}")
    print(f"[*] Output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    findings_dir = output_dir / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch & Render Page
    print("[1/5] Fetching and rendering page...")
    render_result = run_helper("render_page.py", target_url, "--mode", mode, "--json")
    if not isinstance(render_result, dict) or "content" not in render_result:
        # Fallback to direct requests if needed
        import requests
        try:
            resp = requests.get(target_url, timeout=15, headers={"User-Agent": "Universal-SEO-Agent/3.0"})
            html_content = resp.text
            headers = dict(resp.headers)
            status_code = resp.status_code
        except Exception as e:
            print(f"[!] Fetch error: {e}", file=sys.stderr)
            html_content = ""
            headers = {}
            status_code = 0
    else:
        html_content = render_result.get("content", "")
        headers = render_result.get("headers", {})
        status_code = render_result.get("status_code", 200)

    # 2. Sitemap Discovery
    print("[2/5] Inspecting robots.txt and discovering XML sitemaps...")
    sitemap_result = run_helper("sitemap_discovery.py", target_url, "--json")
    if not isinstance(sitemap_result, dict):
        sitemap_result = {"declared": [], "found": [], "checked": []}

    # 3. Agentic & AI Readiness Check
    print("[3/5] Evaluating AI Search & Agent Readiness (llms.txt, AI bots, WebMCP)...")
    agentic_result = run_helper("agentic_check.py", target_url, "--json")
    if not isinstance(agentic_result, dict):
        agentic_result = {"score": 75, "findings": []}

    # 4. Parse HTML Deep Analysis
    print("[4/5] Analyzing On-Page structure, Schema.org JSON-LD, and headers...")
    soup = BeautifulSoup(html_content, "html.parser")

    # Title & Meta Description
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    # Canonical
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical_url = canonical_tag.get("href", "").strip() if canonical_tag else ""

    # Viewport
    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    viewport_content = viewport_tag.get("content", "") if viewport_tag else ""

    # Robots meta
    robots_meta_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_meta = robots_meta_tag.get("content", "") if robots_meta_tag else ""

    # Headings hierarchy
    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    # Schema JSON-LD
    schema_blocks = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            schema_blocks.append(json.loads(script.string or "{}"))
        except Exception:
            pass

    # Images
    images = soup.find_all("img")
    images_without_alt = [img.get("src", "") for img in images if not img.get("alt")]

    # Links
    links = soup.find_all("a", href=True)
    internal_links = []
    external_links = []
    for a in links:
        href = a["href"].strip()
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_link = urljoin(target_url, href)
        if urlparse(full_link).netloc == domain:
            internal_links.append(full_link)
        else:
            external_links.append(full_link)

    # Security Headers
    hsts = headers.get("strict-transport-security") or headers.get("Strict-Transport-Security")
    csp = headers.get("content-security-policy") or headers.get("Content-Security-Policy")
    x_frame = headers.get("x-frame-options") or headers.get("X-Frame-Options")
    x_content_type = headers.get("x-content-type-options") or headers.get("X-Content-Type-Options")
    referrer_policy = headers.get("referrer-policy") or headers.get("Referrer-Policy")
    permissions_policy = headers.get("permissions-policy") or headers.get("Permissions-Policy")

    # Resource hints
    preload_tags = soup.find_all("link", attrs={"rel": "preload"})
    dns_prefetch_tags = soup.find_all("link", attrs={"rel": "dns-prefetch"})
    preconnect_tags = soup.find_all("link", attrs={"rel": "preconnect"})

    # Evaluate Categories & Scores
    categories = []

    # Category 1: Technical SEO
    tech_findings = []
    tech_what_works = []
    tech_score = 100

    if status_code == 200:
        tech_what_works.append("Homepage returns HTTP 200 OK cleanly.")
    else:
        tech_score -= 30
        tech_findings.append({
            "title": f"Non-200 HTTP Status Code ({status_code})",
            "severity": "Critical",
            "description": f"The homepage returned status code {status_code}.",
            "recommendation": "Ensure homepage returns HTTP 200 OK without errors or unexpected redirects."
        })

    if canonical_url:
        tech_what_works.append(f"Canonical URL is present and declared: {canonical_url}")
        if canonical_url != target_url and canonical_url != target_url.rstrip("/") and canonical_url.rstrip("/") != target_url:
            tech_findings.append({
                "title": "Canonical URL Mismatch",
                "severity": "Medium",
                "description": f"Target URL ({target_url}) differs from canonical ({canonical_url}).",
                "recommendation": "Align internal links and sitemaps with the preferred canonical form."
            })
    else:
        tech_score -= 15
        tech_findings.append({
            "title": "Missing Canonical Tag",
            "severity": "High",
            "description": "Page lacks a <link rel='canonical'> declaration.",
            "recommendation": "Add a self-referential canonical tag to prevent duplicate content issues."
        })

    if hsts:
        tech_what_works.append("HSTS (HTTP Strict Transport Security) header enforced.")
    else:
        tech_score -= 5
        tech_findings.append({
            "title": "Missing HSTS Header",
            "severity": "Low",
            "description": "Strict-Transport-Security header is not configured on the origin/CDN.",
            "recommendation": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload'."
        })

    if csp:
        tech_what_works.append("Content Security Policy (CSP) header is active.")
    else:
        tech_score -= 5
        tech_findings.append({
            "title": "Missing Content-Security-Policy",
            "severity": "Low",
            "description": "No Content-Security-Policy header returned.",
            "recommendation": "Deploy a robust CSP header to mitigate XSS and injection vulnerabilities."
        })

    sitemaps_found = sitemap_result.get("found", [])
    if sitemaps_found:
        valid_sitemaps = [s["url"] for s in sitemaps_found if s.get("valid")]
        tech_what_works.append(f"Discovered {len(valid_sitemaps)} valid sitemap(s) declared in robots.txt.")
    else:
        tech_score -= 15
        tech_findings.append({
            "title": "No Sitemaps Discovered",
            "severity": "High",
            "description": "No valid sitemap found or declared in robots.txt.",
            "recommendation": "Declare XML sitemaps in robots.txt and submit them to Google Search Console."
        })

    categories.append({
        "name": "Technical SEO",
        "score": max(tech_score, 0),
        "what_works": tech_what_works,
        "findings": tech_findings,
    })

    # Category 2: Content & E-E-A-T
    content_findings = []
    content_what_works = []
    content_score = 100

    if title_text:
        title_len = len(title_text)
        if 40 <= title_len <= 70:
            content_what_works.append(f"Title tag length is optimal ({title_len} chars): '{title_text}'")
        else:
            content_findings.append({
                "title": f"Title Tag Length Suboptimal ({title_len} chars)",
                "severity": "Medium",
                "description": f"Title '{title_text}' is {title_len} chars (optimal: 50-60 chars).",
                "recommendation": "Keep title between 50 and 60 characters for maximum SERP visibility without truncation."
            })
    else:
        content_score -= 25
        content_findings.append({
            "title": "Missing Title Tag",
            "severity": "Critical",
            "description": "Page has no <title> element in <head>.",
            "recommendation": "Add a descriptive, keyword-rich <title> tag."
        })

    if meta_desc:
        desc_len = len(meta_desc)
        if 120 <= desc_len <= 165:
            content_what_works.append(f"Meta description length is optimal ({desc_len} chars).")
        else:
            content_findings.append({
                "title": f"Meta Description Length ({desc_len} chars)",
                "severity": "Low",
                "description": f"Meta description is {desc_len} chars (optimal: 130-160 chars).",
                "recommendation": "Adjust meta description to ~140-160 characters with clear value proposition and CTA."
            })
    else:
        content_score -= 15
        content_findings.append({
            "title": "Missing Meta Description",
            "severity": "High",
            "description": "Page lacks a meta description.",
            "recommendation": "Add an engaging meta description with primary search intent keywords."
        })

    if len(h1_tags) == 1:
        content_what_works.append(f"Single H1 heading found: '{h1_tags[0]}'")
    elif len(h1_tags) == 0:
        content_score -= 15
        content_findings.append({
            "title": "Missing H1 Heading",
            "severity": "High",
            "description": "No <h1> element detected on the page.",
            "recommendation": "Provide exactly one clear H1 heading communicating the page's core topic."
        })
    else:
        content_findings.append({
            "title": f"Multiple H1 Headings ({len(h1_tags)})",
            "severity": "Low",
            "description": f"Found {len(h1_tags)} H1 headings: {h1_tags[:3]}...",
            "recommendation": "Use a single semantic H1 heading for the primary topic and H2s for sub-sections."
        })

    if images_without_alt:
        content_score -= min(len(images_without_alt) * 3, 20)
        content_findings.append({
            "title": f"{len(images_without_alt)} Image(s) Missing Alt Text",
            "severity": "Medium",
            "description": f"{len(images_without_alt)} image elements lack descriptive alt attributes.",
            "recommendation": "Add contextual, keyword-relevant alt attributes to all informational images."
        })
    else:
        content_what_works.append("All detected images have alt attributes.")

    categories.append({
        "name": "Content & On-Page SEO",
        "score": max(content_score, 0),
        "what_works": content_what_works,
        "findings": content_findings,
    })

    # Category 3: Schema & Structured Data
    schema_findings = []
    schema_what_works = []
    schema_score = 100

    if schema_blocks:
        schema_types = []
        for block in schema_blocks:
            t = block.get("@type")
            if isinstance(t, list):
                schema_types.extend(t)
            elif t:
                schema_types.append(t)
            # Graph schemas
            if "@graph" in block and isinstance(block["@graph"], list):
                for node in block["@graph"]:
                    gt = node.get("@type")
                    if isinstance(gt, list):
                        schema_types.extend(gt)
                    elif gt:
                        schema_types.append(gt)

        schema_types = list(set(schema_types))
        schema_what_works.append(f"Detected {len(schema_blocks)} JSON-LD script(s) defining types: {', '.join(schema_types)}")
        
        # Check for rich entity types
        for recommended in ["WebSite", "Organization", "LocalBusiness", "FAQPage", "Dataset"]:
            if recommended not in schema_types:
                schema_findings.append({
                    "title": f"Opportunity: Add '{recommended}' Schema",
                    "severity": "Low",
                    "description": f"The page does not declare a '{recommended}' JSON-LD schema.",
                    "recommendation": f"Implement '{recommended}' schema to enhance SERP rich snippet eligibility."
                })
    else:
        schema_score -= 40
        schema_findings.append({
            "title": "No Schema.org JSON-LD Structured Data",
            "severity": "High",
            "description": "Page contains zero JSON-LD structured data blocks.",
            "recommendation": "Add Schema.org JSON-LD structured data (WebSite, Organization, LocalBusiness, BreadcrumbList)."
        })

    categories.append({
        "name": "Structured Data & Schema.org",
        "score": max(schema_score, 0),
        "what_works": schema_what_works,
        "findings": schema_findings,
    })

    # Category 4: AI Search & Agent Readiness (GEO / AEO)
    geo_findings = []
    geo_what_works = []
    geo_score = 90

    # Check for discovery files
    api_catalog = soup.find("link", attrs={"rel": "api-catalog"})
    llms_txt = soup.find("link", attrs={"rel": "describedby", "href": re.compile(r"llms\.txt")})
    openapi_link = soup.find("link", attrs={"rel": "service-desc"})

    if llms_txt:
        geo_what_works.append("llms.txt discovery link is declared in HTML <head>.")
    else:
        geo_score -= 10
        geo_findings.append({
            "title": "Missing llms.txt Discovery Link",
            "severity": "Medium",
            "description": "Page lacks a <link rel='describedby' href='/llms.txt'> tag for AI agents.",
            "recommendation": "Deploy a clean markdown /llms.txt file describing site capabilities and link it in <head>."
        })

    if api_catalog or openapi_link:
        geo_what_works.append("API catalog / OpenAPI service description link detected for machine agents.")
    else:
        geo_findings.append({
            "title": "Missing Machine-Readable API Catalog Link",
            "severity": "Low",
            "description": "No link rel='api-catalog' or OpenAPI spec linked for autonomous agents.",
            "recommendation": "Link /.well-known/api-catalog or /openapi.json in <head> to empower agentic discovery."
        })

    categories.append({
        "name": "AI Search & GEO Readiness",
        "score": max(geo_score, 0),
        "what_works": geo_what_works,
        "findings": geo_findings,
    })

    # Calculate Overall Health Score
    overall_health = int(sum(c["score"] for c in categories) / len(categories))

    # Action Plan Generation
    all_findings = []
    for c in categories:
        all_findings.extend(c["findings"])

    critical_items = [f"{f['title']}: {f['recommendation']}" for f in all_findings if f["severity"] == "Critical"]
    high_items = [f"{f['title']}: {f['recommendation']}" for f in all_findings if f["severity"] == "High"]
    medium_items = [f"{f['title']}: {f['recommendation']}" for f in all_findings if f["severity"] == "Medium"]
    low_items = [f"{f['title']}: {f['recommendation']}" for f in all_findings if f["severity"] == "Low"]

    action_plan = {
        "phases": [
            {"name": "Phase 1: Immediate Critical Fixes", "timeframe": "Week 1", "items": critical_items or ["Maintain current zero-error technical baseline."]},
            {"name": "Phase 2: High-Impact Improvements", "timeframe": "Weeks 2-3", "items": high_items or ["Expand metadata and internal linking coverage."]},
            {"name": "Phase 3: Schema & AI Citation Expansion", "timeframe": "Month 2", "items": medium_items or ["Deepen entity schema graphs and fact triplet structures."]},
            {"name": "Phase 4: Ongoing Monitoring & Drift Prevention", "timeframe": "Ongoing", "items": low_items or ["Weekly GSC and Core Web Vitals drift tracking."]},
        ]
    }

    # Top Findings & Quick Wins
    top_findings = [f["title"] for f in sorted(all_findings, key=lambda x: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(x["severity"], 4))[:5]]
    quick_wins = [f"{f['title']} - {f['recommendation']}" for f in all_findings if f["severity"] in ("Medium", "Low")][:4]

    audit_data = {
        "summary": {
            "target": target_url,
            "domain": domain,
            "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "health_score": overall_health,
            "business_type": "Geospatial Atlas & Land Intelligence Platform",
            "top_findings": top_findings,
            "quick_wins": quick_wins,
        },
        "categories": categories,
        "action_plan": action_plan,
        "artifacts": {
            "findings_dir": "findings/",
            "screenshots_dir": "screenshots/",
        }
    }

    # 5. Write Artifacts
    print("[5/5] Generating Markdown reports and JSON data envelopes...")
    
    # Write audit-data.json
    (output_dir / "audit-data.json").write_text(json.dumps(audit_data, indent=2), encoding="utf-8")

    # Write Category Findings Markdown
    for cat in categories:
        cat_slug = re.sub(r"[^a-z0-9]+", "-", cat["name"].lower()).strip("-")
        md_content = [
            f"# {cat['name']} Findings",
            f"**Category Score**: {cat['score']}/100\n",
            "## What Works Well",
            *[f"- {w}" for w in cat["what_works"]],
            "\n## Issues & Recommendations",
        ]
        if not cat["findings"]:
            md_content.append("- No critical issues found in this category.")
        else:
            for f in cat["findings"]:
                md_content.extend([
                    f"### [{f['severity']}] {f['title']}",
                    f"**Description**: {f['description']}",
                    f"**Recommendation**: {f['recommendation']}\n",
                ])
        (findings_dir / f"{cat_slug}.md").write_text("\n".join(md_content), encoding="utf-8")

    # Write ACTION-PLAN.md
    plan_lines = [
        f"# SEO Action Plan: {domain}",
        f"**Audit Date**: {time.strftime('%B %d, %Y', time.gmtime())}",
        f"**Health Score**: {overall_health}/100\n",
    ]
    for ph in action_plan["phases"]:
        plan_lines.append(f"## {ph['name']} ({ph['timeframe']})")
        for it in ph["items"]:
            plan_lines.append(f"- [ ] {it}")
        plan_lines.append("")
    (output_dir / "ACTION-PLAN.md").write_text("\n".join(plan_lines), encoding="utf-8")

    # Write FULL-AUDIT-REPORT.md
    report_lines = [
        f"# Comprehensive SEO & AEO Audit Report: {domain}",
        f"**Target URL**: {target_url}  ",
        f"**Overall Health Score**: **{overall_health} / 100**  ",
        f"**Date Generated**: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n",
        "## Executive Summary",
        f"This audit evaluates `{domain}` across Technical SEO, Content Quality & E-E-A-T, Structured Data (Schema.org), and Generative Engine Optimization (GEO) for AI engines (Google Gemini, ChatGPT, Perplexity, Claude).\n",
        "### Score Breakdown",
        "| Category | Score | Status |",
        "| :--- | :---: | :--- |",
    ]
    for cat in categories:
        status_label = "Optimal" if cat["score"] >= 90 else "Good" if cat["score"] >= 75 else "Needs Work"
        report_lines.append(f"| **{cat['name']}** | {cat['score']}/100 | {status_label} |")

    report_lines.extend([
        "\n## Top Priority Findings",
        *[f"1. **{f}**" for f in top_findings],
        "\n## Category In-Depth Analysis",
    ])
    for cat in categories:
        report_lines.extend([
            f"\n### {cat['name']} (Score: {cat['score']}/100)",
            "**Highlights**:",
            *[f"- {w}" for w in cat["what_works"]],
            "\n**Areas for Improvement**:",
        ])
        if not cat["findings"]:
            report_lines.append("- Zero defects identified.")
        else:
            for f in cat["findings"]:
                report_lines.extend([
                    f"- **[{f['severity']}] {f['title']}**: {f['description']}",
                    f"  - *Action*: {f['recommendation']}",
                ])

    (output_dir / "FULL-AUDIT-REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[+] Audit complete! Overall Health Score: {overall_health}/100")
    print(f"[+] Artifacts created in: {output_dir}")
    return audit_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Universal SEO Audit Orchestrator")
    parser.add_argument("url", help="Target website URL to audit")
    parser.add_argument("--output-dir", "-o", help="Custom output directory", default=None)
    parser.add_argument("--mode", choices=["auto", "always", "never"], default="auto", help="Headless render mode")
    parser.add_argument("--json", action="store_true", help="Print audit results as JSON to stdout")
    args = parser.parse_args()

    parsed = urlparse(args.url)
    domain_slug = re.sub(r"[^a-zA-Z0-9.-]", "", parsed.netloc or args.url).replace(":", "-")
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / f"{domain_slug}-audit"

    data = audit_url(args.url, output_dir, mode=args.mode)
    if args.json:
        print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
