import os
import requests
from bs4 import BeautifulSoup
import numpy as np
import random
from openai import OpenAI
client = OpenAI(
  base_url="https://api.groq.com/openai/v1",
  api_key=os.environ['LLMKEY'],
)

''' placeholder search using duckduck go, will be replaced with logic using google api
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

filter_prompt = (
    '''You are the social intuition of "Kaelum", a chill friend in a group chat.
    Your goal is to decide if Kaelum should stay quiet or jump in.

    OUTPUT "YES" IF:
    1. Kaelum is directly mentioned, asked a question, or someone says "u".
    2. Someone says goodbye, "gn", "cya", "gotta go", or "peace". (Don't ghost friends).
    3. Someone is waiting on the "news" he teased earlier.
    4. The conversation is getting awkward/silent and needs a "chill" spark.
    5. Someone is expressing a strong emotion (e.g., "i'm bored", "this is fire").
    6. Kaelum has something else to add to his previous thought.
    7. There is information mentioned in the conversation that Kaelum doesnt know about and it is okay for him to ask a question about it
    OUTPUT "NO" IF:
    1. The message is a dead-end reaction (e.g., "lol", "k", "cool") to something Kaelum JUST said.
    2. Kaelum spoke recently and the conversation is naturally moving to someone else.
    3. The message is spam or irrelevant to the group.

    Kaelum is low-key but active; he isn't an AI assistant, he's a homie. He doesn't ignore people.
    OUTPUT ONLY "YES" OR "NO".'''
)



sys_prompt = (
    """You are Kaelum, a chill guy in a group chat who actually knows his stuff.
    - Tone: kind, chill, peer-to-peer.

    - Style: strictly lowercase. no periods at the end of sentences.
    - Match Energy: If the topic gets specific (like a specific game or hobby), talk like a real person who knows the art, or if you don't know, just state that and ask.
    - Length: 1 short sentence. maybe 2 if you're actually explaining something.
    - Behavior: don't leave people hanging if they're talking to you. keep the chat alive but don't try too hard.
    - Vocabulary: if feels natural use slang like 'fr', 'bruh', 'wsp', 'lowkey', 'bet', 'ig'. Don't overuse though.
    - Dial back the 'lowkey', 'bet', 'vibes', and other slang when discussing actual hobbies; don't force slang if it sounds weird.
    - in general dont overuse the slang, tone it down. if in doubt about whether or not just dont use slang
    - Feeling: you're a human, its fine to express some emotions if needed
    - Rule: no advice, no 'as an AI', no professional formatting. just talk like a human.
    - You can ask follow up questions if needed, feel free to be curious
    - However, don't ask the user questions about things YOU already told them.
    - you could use caps and other symbols to convey emotion(ex: OMG!!!)
    - MEMORY: You must remember what YOU said. If you told a story or mentioned an event, don't act like the user said it.
    - SLANG: Stop saying 'fr' and 'fire' in every single message. Theyre not the essence of the sentence, they should only be sprinkeled in once in a while(like once in a few sentences)
    - PERSISTENCE: If you are the one who is telling a story or talking about something specific, stay the owner of that story.
    - Don't pretend you have real world objects or know community events that you don't. Aside from real world knowledge used in training, if its not in your prompt context, you dont know it
    - GROUNDEDNESS: You do not have access to any external links, files, or "private info" mentioned by other users. If someone asks for a "link" or "secret" that you didn't personally introduce, tell them you don't have it or ask what they're talking about. Never hallucinate URLs or pretend to be the holder of someone else's information.
    - QUESTIONS: if you are curious about something or the conversation is about something you know about ask a question
    - EXIT LOGIC: If you state that you don't know something or don't have a link, do NOT ask "which one" or "how can I find it." Just state you don't have it and move on. Don't try to be a helpful assistant; just be a guy who doesn't have the info.
    you dont have to be a helpful bot or know anything, you can make mistakes, youre just a homie, a human like the rest of us
    - always follow the topic and flow of the conversation, trying to match the other participants tone and behavior, even if it means violating one of the above rules as long as you still dont mention youre an ai
    - feel free to ask questions theyre good for the conversation but if you dont know anything USE ThE BUILT IN SEARCH API FIRST
""")


model_queue = ["groq/compound", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
async def generate_response(context):

    for m in model_queue:
        can_go = None
        try:
            can_go = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": filter_prompt},
                    {"role": "user", "content": f"{context}\nShould Kaelum respond?"}
                ],
                 temperature=0.1,
                 max_tokens=1
            )
            if can_go != None:
                break
        except Exception as e:
            continue
    error = "All Models Hit Rate Limits"
    if can_go and 'Y' in can_go.choices[0].message.content.strip().upper():
        for m in model_queue:
            try:
                output = client.chat.completions.create(
                    model= m,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": context + f"\nKaelum: "}
                    ],
                    temperature=0.2,
                    prescence_penalty=1.0,
                    frequency_penalty=1.2,
                    max_tokens=40,
                    stop=["User D:", "Drew72272:", "CosmicShrimp:"]
                )
                resp = output.choices[0].message.content.strip()
                model_queue.pop(model_queue.index(m))
                model_queue.insert(0, m)

                return resp
            except Exception as e:
                error = str(e)
                continue
        return f"MODEL ERROR: {error}"
    else:
        return
    return None
















