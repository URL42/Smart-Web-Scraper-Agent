# 🧠 Smart Scraper Agent

An AI-powered web agent built with OpenAI + Playwright + Streamlit.

## 💡 What It Does

- Takes your natural-language query (e.g. “What’s on Notion’s pricing page?”)
- GPT-4.1 chooses the best URL
- Scrapes the live website using Playwright (human-like browsing)
- Exports the text to a `.txt` file in `/scrapes`
- GPT summarizes and responds in the UI

## 🧪 Demo Prompts

- `What is the latest blog post on openai.com?`
- `What’s the top article on nytimes.com right now?`
- `What are the pricing options on Notion’s website?`

## 📦 Install

```bash
git clone https://github.com/your-username/smart-scraper-agent.git
cd smart-scraper-agent
python3 -m venv venv && source venv/bin/activate
pip install -r install.txt
playwright install
cp .env.template .env
```

## 🚀 Run It

```
streamlit run smart_scraper_app.py
```

## 📝 Output
Scraped content is saved to /scrapes/ with timestamped .txt files.

## 🔐 API Key
Rename .env.template to .env and add your OpenAI API key.

## 🛡 Anti-Scraping Features
- Human-like delays and scrolling
- Randomized user agents
- Custom browser fingerprint

### MIT License

Copyright (c) 2025 Anthony Holmes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      
copies of the Software, and to permit persons to whom the Software is          
furnished to do so, subject to the following conditions:                       

The above copyright notice and this permission notice shall be included in     
all copies or substantial portions of the Software.                            

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR     
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,       
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER         
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN      
THE SOFTWARE.
