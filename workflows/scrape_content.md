---
description: How to scrape and extract content from a website for tweet repurposing
---

## Objective
Extract the main text content from a URL (article, blog post, newsletter) so it can be summarised or repurposed into tweets.

## Required Inputs
- Target URL to scrape
- Optional: specific CSS selector for the content area

## Steps

1. Check if the target URL is accessible
   - Simple test: `curl -I <url>` or run the scrape tool and check for errors

2. Scrape the page content
   ```
   python tools/scrape_website.py --url "https://example.com/article" --output .tmp/scraped.txt
   ```
   > **Note:** `tools/scrape_website.py` — to be built. See "Next Tools to Build" below.

3. Review the extracted content
   - Open `.tmp/scraped.txt`
   - Check that the main article body was captured and boilerplate was stripped

4. Pass content to the tweet generator
   ```
   python tools/generate_tweets.py --input .tmp/scraped.txt --count 5 --output .tmp/tweets.json
   ```
   > **Note:** `tools/generate_tweets.py` — to be built.

5. Review and select tweets
   - Open `.tmp/tweets.json`
   - Choose the best candidates for posting

6. Post approved tweets
   - Follow the `post_tweet.md` workflow

## Expected Output
- `.tmp/scraped.txt` — clean article text
- `.tmp/tweets.json` — LLM-generated tweet candidates

## Error Handling
| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `403 Forbidden` / `401` | Site blocks scrapers | Use Playwright (headless browser) instead of requests |
| Empty content | Wrong selector | Inspect page HTML, pass `--selector` with correct CSS selector |
| Garbled text | JavaScript-rendered content | Switch to Playwright: `--js` flag in scrape tool |
| Rate limited | Too many requests | Add `time.sleep(2)` between requests in the tool |

## Notes
- Always respect `robots.txt` — check before scraping
- Paywalled articles may require login; don't attempt to bypass
- Prefer RSS feeds when available (much simpler than scraping)
- Content saved to `.tmp/` is disposable — don't treat it as a deliverable

## Next Tools to Build
1. `tools/scrape_website.py` — extract article text (requests + BeautifulSoup, fallback to Playwright)
2. `tools/generate_tweets.py` — call OpenAI/Anthropic to create tweet variants from content
