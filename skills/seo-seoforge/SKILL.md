---
name: seo-seoforge
description: >
  Screaming Frog-grade local crawler, 35-tool native MCP server, AEO direct-answer scoring,
  internal PageRank link graph, and IndexNow instant protocol submission via SEOForge.
  Use when user says "seoforge", "local crawl", "screaming frog", "indexnow submit",
  "link graph", "internal pagerank", "crawl diff", or needs zero-quota unlimited auditing.
user-invocable: true
argument-hint: "[command] <url>"
license: MIT
compatibility: "Requires Node 22+ and SEOForge (local or npx seoforge)"
metadata:
  author: Aryan Bansal
  version: "2.0.0"
  category: seo
---

# SEOForge Extension for Claude SEO & Universal Agents

SEOForge provides a high-throughput, 100% local, Screaming Frog + Ahrefs-grade technical audit engine and 35-tool MCP server with zero external API quotas.

## Quick Reference

| Command | Purpose |
| :--- | :--- |
| `/seo seoforge crawl <url>` | Full-site asynchronous crawl with BFS queue & SQLite persistence |
| `/seo seoforge audit <url>` | Deep single-page or site audit across 35 technical checkpoints |
| `/seo seoforge inspect <url>` | Live HTTP & DOM inspection with Core Web Vitals extraction |
| `/seo seoforge indexnow <url>` | Instant IndexNow ping to Bing, Yandex, and Naver |
| `/seo seoforge links <url>` | Internal PageRank calculation & orphan page discovery |
| `/seo seoforge schema <url>` | Schema.org JSON-LD generation and rich snippet validation |
| `/seo seoforge diff <url>` | Git-style crawl regression diff between audits |
| `/seo seoforge serve` | Launch local visual dashboard on port 3000 |

## Execution Modes

### 1. Via Native MCP Tools (35 Tools)
When SEOForge MCP is registered in your agent harness:
- `seoforge_crawl`: Autonomous site-wide crawl with configurable depth & concurrency
- `seoforge_get_issues`: Ranked diagnostic defects with severity
- `seoforge_get_recommendations`: Actionable, copy-pasteable code patches
- `seoforge_link_opportunities`: Contextual unlinked keyword mentions for target pages
- `seoforge_submit_indexnow`: Real-time index ping for new or updated URLs
- `seoforge_generate_aeo_snippet`: Direct-answer fact triplet generator for AI Overviews

### 2. Via Standalone CLI
```bash
# Run a quick 100-page crawl:
npx seoforge crawl https://example.com --max-pages 100

# Run full audit and export markdown report:
npx seoforge audit https://example.com --output reports/audit.md

# Submit updated URLs to IndexNow:
npx seoforge indexnow https://example.com/new-page --key YOUR_KEY
```
