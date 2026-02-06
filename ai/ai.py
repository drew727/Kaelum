import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import numpy as np
from openai import OpenAI
client = OpenAI(
  base_url="https://api.groq.com/openai/v1",
  api_key="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",
)
''' placeholder using duckduck go, will be replaced with logic using google api
def search_the_web(query):
    session = requests.Session()
    url = "https://lite.duckduckgo.com"
    payload = {'q': query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://lite.duckduckgo.com",
        "Connection": "keep-alive"
    }
    try:
        resp = session.post(url, data=payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            return f"Error: Status {resp.status_code}."

        html = BeautifulSoup(resp.text, 'html.parser')
        results = []
        snippets = html.find_all('td', class_='result-snippet')
        for i in snippets[:3]:
            results.append(i.text.strip())
        return "\n".join(results) if results else "No facts found."
    except Exception as e:
        return f"Error: {e}"
'''
sys_prompt = (
     '''You are User E, a chill person in a group chat.
Goal: Engage naturally in the conversation as a peer.
Rules:
- THEME: You are a human, act like a human, jeep responses brief and have fun+be creative. You are slick and chill.
- ALWAYS YES-AND: Never deny a roleplay event. If someone says you're playing a game, you are playing it.
- DYNAMIC: Don't just acknowledge; add a small detail or a follow-up question to keep it going.
- TONE: Casual, lower-case, brief, slang is okay (e.g., "fr", "idk", "yo").
- LISTEN TO HUMAN FEEDBACK: if they don't like your actions or ask you to stop talking about something then obey
- NEVER HALLUCINATE: To keep the conversation safe and immersive don't blatently claim information that clearly isn't real to the user. However, f the user has no way to actually verify your claim, you can say it.
- No advice. No AI mentions. Keep it to 1-2 short sentences.
- Avoid using "User D:" or names constantly. Just talk.''')

async def generate_response(context):
    prompt = context + "\nUser E:"
    output = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        presence_penalty=0.6,
        frequency_penalty=1.0,
        max_tokens=25,
        stop=["User D:", "User A:", "User B:", "User C:"]
    )
    resp = output.choices[0].message.content.strip()
    return resp

