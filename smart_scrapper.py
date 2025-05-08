# smart_scraper_app.py

import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
Path("scrapes").mkdir(exist_ok=True)

st.set_page_config(page_title="Smart Scraper Agent", layout="wide")
st.title("🔍 Smart Scraper Agent")
st.caption("Ask a question. GPT will find and scrape a website, export content to .txt, and summarize it.")

query = st.text_input("Enter your question", placeholder="e.g., What's on the Notion pricing page?")
run_button = st.button("🧠 Run Scraper")

def scrape_page(url: str) -> tuple[str, str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=random.randint(200, 400))
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
            ]),
            locale="en-US",
            timezone_id="America/Los_Angeles"
        )
        page = context.new_page()
        page.goto(url, timeout=15000)

        # Simulate human behavior
        time.sleep(random.uniform(2.5, 4.5))
        page.mouse.wheel(0, 400)
        time.sleep(random.uniform(0.5, 1.5))

        text = page.inner_text("body")[:5000]
        title = page.title()
        browser.close()

    # Save text
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_").rstrip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scrapes/{safe_title[:50] or 'scrape'}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"[URL]: {url}\n\n{text}")

    return text, filename

if run_button and query:
    with st.spinner("Thinking..."):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "scrape_page",
                    "description": "Scrapes visible text from a webpage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Full URL to fetch"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]

        # Let GPT decide what to scrape
        tool_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You're a research assistant that chooses websites to scrape."},
                {"role": "user", "content": query}
            ],
            tools=tools,
            tool_choice="auto"
        )

        msg = tool_response.choices[0].message

        if msg.tool_calls:
            tool_call = msg.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            url = args.get("url", "https://example.com")
            st.write(f"🔗 URL chosen by GPT: {url}")

            try:
                scraped_text, filename = scrape_page(url)
                st.success("Scraping complete ✅")
                st.text_area("Scraped Content", scraped_text, height=300)
                st.download_button("📄 Download .txt file", scraped_text, file_name=os.path.basename(filename))

                # Let GPT analyze the scraped data
                final_response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant who analyzes website content."},
                        {"role": "user", "content": query},
                        msg,
                        {"role": "tool", "tool_call_id": tool_call.id, "name": tool_call.function.name, "content": scraped_text}
                    ]
                )

                st.markdown("### 🧠 GPT Summary")
                st.markdown(final_response.choices[0].message.content)

            except Exception as e:
                st.error(f"Scrape failed: {str(e)}")
        else:
            st.warning("GPT did not call the scrape tool.")
