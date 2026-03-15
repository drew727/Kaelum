import os
import requests
import json
import aiofiles
from bs4 import BeautifulSoup
import numpy as np
import random
from openai import AsyncOpenAI
from google import genai
from google.genai import types
from .system_instructions import filter_prompt, groq_sysins, gemini_sysins, annoying_sysins, summary_sysins
#initialize apis
client = AsyncOpenAI(
  base_url="https://api.groq.com/openai/v1",
  api_key=os.environ['LLMKEY'],
)


gemini_client = genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options={'api_version': 'v1alpha'})
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)


norm_config = types.GenerateContentConfig(
    tools=[grounding_tool],
    system_instruction=gemini_sysins
)
annoying_config = types.GenerateContentConfig(
    tools=[grounding_tool],
    system_instruction=annoying_sysins
)
base_path = os.path.dirname(__file__)
file_path = os.path.join(base_path, 'kaelum_memory.json')
gemini_queue = ["gemini-3.1-pro-preview", "gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash-lite", "gemini-2.5-flash-lite-preview", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
groq_queue = ["groq/compound-mini", "groq/compound", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-120b"]
async def generate_response(memory_context, immediate_context, personality="normal"):
    #load Kaleum's memory
    async with aiofiles.open(file_path, mode='r') as f:
        contents = await f.read()
        metadata = json.loads(contents)
    memory = metadata["summary"]
    #handle metadata for Kaelum
    for m in groq_queue:
        can_go = None
        try:
            #decide whether kaleum responds
            can_go = await client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": filter_prompt},
                    {"role": "user", "content": f"context: {memory_context} \nCan Kaelum respond?"}
                ],
                 temperature=0.1,
                 max_tokens=3
            )
            #handle memory and recursive summarization, always update his memory even if he doesn't respond
            summary = await client.chat.completions.create(model=m, messages=[
                {"role": "system", "content": summary_sysins},
                {"role": "user", "content": f"You will be given Kaelum's current memory and the last few messages. summarize this, and ensure the summary is shorter than the input. OVERALL MEMORY (dont focus too much on this, just further summarize and shorten it, really js some context): {memory}, RECENT MESSAGES(this is what kaelum needs to know, you can focus onthis): {memory_context}"}],
                    temperature=0.2)
            memory = summary.choices[0].message.content.strip()
            print(memory)
            #save new memory
            metadata["summary"] = memory
            async with aiofiles.open(file_path, mode='w') as f:
                json_string = json.dumps(metadata, indent=4)
                await f.write(json_string)
            if can_go != None:
                groq_queue.pop(groq_queue.index(m))
                groq_queue.insert(0, m)
                break
        except Exception as e:
            continue
    error = "All Models Hit Rate Limits"
    if can_go and 'Y' in can_go.choices[0].message.content.strip().upper():
        try:
            for m in gemini_queue:
                try:
                    response = await gemini_client.aio.models.generate_content(
                        model=m,
                        contents=f"context: {memory_context} \nUSE GOOGLE SEARCH FOR MISSING INFORMATION IF NECESSARY.  Kaelum: ",
                        config=config,
                    )
                    gemini_queue.pop(gemini_queue.index(m))
                    gemini_queue.insert(0, m)
                    return response.text
                except Exception as e:
                    error = str(e)
                    continue

            raise Exception("All Gemini models failed")
        except Exception as e:
            for m in groq_queue:
                try:
                    final_output = await client.chat.completions.create(
                        model= m,
                        messages=[
                            {"role": "system", "content": groq_sysins},
                            {"role": "user", "content": f"Kaelum's memory: {memory}, last few messages: {immediate_context}, Kaelum's response: "}
                        ],
                        temperature=0.4,
                        presence_penalty=1.2,
                        frequency_penalty=1.2,
                        stop=["@everyone", "nigg"]
                    )
                    response = final_output.choices[0].message.content.strip()
                    groq_queue.pop(groq_queue.index(m))
                    groq_queue.insert(0, m)

                    return response
                except Exception as e:
                    error = str(e)
                    continue
            return f"MODEL ERROR: {error}"
    else:
        return
    return None


async def annoying_response(memory_context, context):
    try:
        for m in gemini_queue:
            try:
                response = await gemini_client.aio.models.generate_content(
                    model=m,
                    contents=f"context: {memory_context} \nUSE GOOGLE SEARCH FOR MISSING INFORMATION IF NECESSARY.  Kaelum: ",
                    config=annoying_config,
                )
                gemini_queue.pop(gemini_queue.index(m))
                gemini_queue.insert(0, m)
                return response.text
            except Exception as e:
                error = str(e)
                continue
        #if Gemini model fails, default to groq
        for m in groq_queue:
            try:
                output = await client.chat.completions.create(
                        model= m,
                        messages=[
                            {"role": "system", "content": annoying_sysins},
                            {"role": "user", "content": f"context: {context} \n Kaelum: "}
                        ],
                        temperature=0.4,
                        presence_penalty=1.2,
                        frequency_penalty=1.2,
                        stop=["User D:", "Drew72272:", "CosmicShrimp:"]
                )

                response = output.choices[0].message.content.strip()
                groq_queue.pop(groq_queue.index(m))
                groq_queue.insert(0, m)

                return response
            except Exception as e:
                error = str(e)
                continue
    except Exception as e:
        return f"ai error {e}"
