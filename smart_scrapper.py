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
Path("summaries").mkdir(exist_ok=True)
HISTORY_FILE = Path("history.json")

st.set_page_config(page_title="Smart Scraper Agent", layout="wide")
st.title("🔍 Smart Scraper Agent")
st.caption("Ask a question. GPT will scrape a website, export content, and summarize it.")

query = st.text_input("Enter your question", placeholder="e.g., What's on the Notion pricing page?")
run_button = st.button("🧠 Run Scraper")

# Load scrape history
history = []
if HISTORY_FILE.exists():
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)

# Show scrape history
with st.expander("📜 Scrape History", expanded=False):
    if history:
        for item in reversed(history[-10:]):
            st.markdown(f"**Query**: {item['query']}")
            st.markdown(f"**URL**: {item['url']}")
            st.markdown(f"**Saved file**: `{item['filename']}`")
            st.markdown(f"**Summary**: {item['summary'][:200]}...")
            st.markdown("---")
    else:
        st.write("No history yet.")

def scrape_page(url: str) -> tuple[str, str]:
    from datetime import datetime
    from pathlib import Path
    Path("scrapes").mkdir(exist_ok=True)

    profile_dir = "/tmp/playwright-profile"  # Persistent profile directory

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=False,
                slow_mo=random.randint(200, 400),
                viewport={"width": 1280, "height": 800},
                locale="en-US"
            )
            page = browser.new_page()
            page.goto(url, timeout=15000)

            # Simulate human behavior
            time.sleep(random.uniform(2.5, 4.5))
            page.mouse.wheel(0, 400)
            time.sleep(random.uniform(0.5, 1.5))

            # Extract page text
            text = page.inner_text("body")[:5000]
            title = page.title()

            # CAPTCHA/Login detection
            #if any(term in text.lower() for term in ["captcha", "verify you are human", "sign in", "log in", "access denied"]):
            #    st.warning("⚠️ CAPTCHA or login detected. Please complete it manually in the browser.")
            #    page.pause()  # You interact, then resume
            #    text = page.inner_text("body")[:5000]
            #    title = page.title()

            browser.close()

        except Exception as e:
            browser.close()
            raise RuntimeError(f"Scraping failed or blocked: {str(e)}")

    # Save to .txt file
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_").rstrip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scrapes/{safe_title[:50] or 'scrape'}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"[URL]: {url}\n\n{text}")
    return text, filename

def save_summary_md(summary: str, query: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summaries/summary_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"## Query\n{query}\n\n## Summary\n{summary}")
    return filename

if run_button and query:
    with st.spinner("Thinking..."):
        # Step 1: GPT chooses a URL to scrape
        tools = [{
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
        }]
        tool_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You're a research assistant that chooses relevant websites to scrape."},
                {"role": "user", "content": f"""
Your only task is to pick a real, full URL to scrape in order to answer the following question: 
'{query}'

Do not attempt to answer the question directly. Only respond by calling the scrape_page tool with the appropriate URL.
"""}
            ],
            tools=tools,
            tool_choice="auto"
        )
        tool_msg = tool_response.choices[0].message
        if tool_msg.tool_calls:
            tool_call = tool_msg.tool_calls[0]
            url = json.loads(tool_call.function.arguments).get("url", "https://example.com")
            st.write(f"🔗 URL chosen by GPT: {url}")

            # Step 2: Scrape the content
            try:
                scraped_text, filename = scrape_page(url)
                st.success("Scraping complete ✅")
                st.text_area("Scraped Content", scraped_text, height=300)
                st.download_button("📄 Download .txt file", scraped_text, file_name=os.path.basename(filename))
            except Exception as e:
                st.error(str(e))
                st.stop()

            # Step 3: Sanitize the scrape
            clean_response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a smart assistant that removes boilerplate and extracts just the main content."},
                    {"role": "user", "content": f"Clean up this scraped content and return only the relevant parts:\n\n{scraped_text}"}
                ]
            )
            cleaned_text = clean_response.choices[0].message.content

            # Step 4: Summarize based on tool_call OR fallback
            if tool_msg.tool_calls:
                final_response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes web content."},
                        {"role": "user", "content": query},
                        tool_msg,
                        {"role": "tool", "tool_call_id": tool_call.id, "name": tool_call.function.name, "content": cleaned_text}
                    ]
                )
                summary = final_response.choices[0].message.content
            else:
                final_response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes web content."},
                        {"role": "user", "content": f"{query}\n\nHere is the content to summarize:\n\n{cleaned_text}"}
                    ]
                )
                summary = final_response.choices[0].message.content

            st.markdown("### 🧠 GPT Summary")
            st.markdown(summary)

            # Step 5: Save summary + log history
            save_summary_md(summary, query)
            history.append({
                "query": query,
                "url": url,
                "filename": filename,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            })
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

            # Step 6: Follow-up Q&A
            follow_up = st.text_input("Ask a follow-up question based on this scrape:")
            if follow_up:
                follow_response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "You are continuing a conversation based on a scraped page."},
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": summary},
                        {"role": "user", "content": follow_up}
                    ]
                )
                st.markdown("### 💬 Follow-up Answer")
                st.markdown(follow_response.choices[0].message.content)
        else:
            st.warning("⚠️ GPT did not return a tool call. Try rephrasing the question.")

            except Exception as e:
                st.error(f"Scrape failed: {str(e)}")
        else:
            st.warning("GPT did not call the scrape tool.")
