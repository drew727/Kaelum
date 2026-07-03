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
from .system_instructions import filter_prompt, groq_sysins, gemini_sysins, annoying_sysins, summary_sysins, san_diego_sysins, depressed_sysins
from dotenv import load_dotenv
from membrane import MembraneClient, Sensitivity, TrustContext, MemoryType
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# load env vars
load_dotenv()

#initialize membrane client
membrane_client = MembraneClient("localhost:9090")

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

async def membrane_generate_response(memory_context, immediate_context, personality="normal", user_id=None, user_name=None):
    # remember IMMEDIATE CONTEXT IS ONLY 1, MEMORY_CONTEXT IS ONLY 10

    for m in groq_queue:
        can_go = None
        try:
            #decide whether kaleum responds
            can_go = await client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": filter_prompt},
                    {"role": "user", "content": f"""

                        Recent messages:
                        {memory_context}

                        Should Kaelum respond? (using previous memory as some bg information about context and deciding based on new messages)
                        """}
                ],
                 temperature=0.15,
                 max_tokens=3
            )

            #write memory(most recent message) into membrane. This will compile over time
            summary_with_user = immediate_context
            tags = ["recent", "conversation", "thinking background"]
            if user_id:
                tags.append(f"user:{user_id}")
            record = membrane_client.ingest_event(source="chat", event_kind="recent message", ref="kaelum-session", summary=summary_with_user, scope="kaelum", tags=tags)

            if can_go != None:
                groq_queue.pop(groq_queue.index(m))
                groq_queue.insert(0, m)
                break
        except Exception as e:
            continue
    error = "All Models Hit Rate Limits"
    decision_text = ""
    if can_go and can_go.choices:
        decision_text = (can_go.choices[0].message.content or "").strip()

    should_respond = not decision_text or 'Y' in decision_text.upper()
    if can_go and should_respond:
        #generate query
        query = None
        for m in groq_queue:
            try:
                task_descriptor = await client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role": "system", "content": "Generate a brief search query (3-5 words) describing what information the user, Kaelum, would need to know in order to respond based on recent messages."
                        " The query should be specific enough to retrieve relevant information from a vector database, but broad enough to capture all relevant information."},
                        {"role": "user", "content": memory_context}
                   ],
                    temperature=0.3,
                    max_tokens=20
                )
                query = task_descriptor.choices[0].message.content.strip()
                print(query)
                break

            except Exception as e:
                error = str(e)
                continue
        if not query:
            return f"memory retrieval failed, MODEL ERROR: {error}"
        #now retrieve memories
        retrieved_memories = membrane_client.retrieve(query, limit=5)
        memory_text = "\n".join([r.summary for r in retrieved_memories])
        try:
            for m in gemini_queue:
                try:
                    response = await gemini_client.aio.models.generate_content(
                        model=m,
                        contents=f"context: {memory_context}, some retrieved memories to help fill missing information: {memory_text}, Kaelum's response: ",
                        config=norm_config,
                    )
                    gemini_queue.pop(gemini_queue.index(m))
                    gemini_queue.insert(0, m)
                    print(response.text)
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
                            {"role": "user", "content": f"""
                                Recent messages:
                                {memory_context}
                                Some retrieved memories to help fill missing information:
                                {memory_text}
                                What would Kaelum say next?"""}
                        ],
                        temperature=1.0,
                        stop=["@everyone", "nigg"]
                    )
                    response = final_output.choices[0].message.content.strip()
                    groq_queue.pop(groq_queue.index(m))
                    groq_queue.insert(0, m)
                    #write memory record into membrane now
                    print("response:\n" + final_output.choices[0].message.content.strip())
                    return response
                    
                except Exception as e:
                    error = str(e)
                    continue
            return f"MODEL ERROR: {error}"
    else:
        return
    return None

#original logic
async def generate_response(memory_context, immediate_context, personality="normal"):
    #load Kaleum's memory
    async with aiofiles.open(file_path, mode='r') as f:
        contents = await f.read()
        metadata = json.loads(contents)
    memory = metadata.get("normal_summary") or metadata.get("summary") or ""
    #handle metadata for Kaelum
    for m in groq_queue:
        can_go = None
        try:
            #decide whether kaleum responds
            can_go = await client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": filter_prompt},
                    {"role": "user", "content": f"""
Previous memory:
{memory}

New messages:
{memory_context}

Should Kaelum respond? (using previous memory as some bg information about context and deciding based on new messages)
"""}
                ],
                 temperature=0.1,
                 max_tokens=3
            )
            #handle memory and recursive summarization, always update his memory even if he doesn't respond
            summary = await client.chat.completions.create(model=m, messages=[
                {"role": "system", "content": summary_sysins},
                {"role": "user", "content": f"""
Previous memory:
{memory}

New messages:
{memory_context}

Update Kaelum's memory summary.
"""}],
                    temperature=1.5)
            memory = summary.choices[0].message.content.strip()
            print(memory)
            #save new memory
            metadata["normal_summary"] = memory
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
                        config=norm_config,
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
                            {"role": "user", "content": f"""
Conversation summary:
{memory}

Recent messages:
{immediate_context}

What would Kaelum say next?
"""}
                         #   {"role": "user", "content": f"Kaelum's memory: {memory}, last few messages: {immediate_context}, Kaelum's response: "}
                        ],
                        temperature=1.5,
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


async def annoying_response(memory_context, context, user_id=None, user_name=None):
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
                        temperature=0.95,
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
        logging.exception(e)
        return f"ai error {e}"

async def san_diego_response(memory_context, immediate_context, personality="normal"):
    async with aiofiles.open(file_path, mode='r') as f:
        contents = await f.read()
        metadata = json.loads(contents)
    memory = metadata.get("san_diego_summary") or metadata.get("summary") or ""
    #handle metadata for Kaelum
    for m in groq_queue:
        can_go = None
        try:
            #decide whether kaleum responds
            can_go = await client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": filter_prompt},
                    {"role": "user", "content": f"""
Previous memory:
{memory}

New messages:
{memory_context}

Should Kaelum respond?
"""}
                ],
                 temperature=0.1,
                 max_tokens=3
            )
            #handle memory and recursive summarization, always update his memory even if he doesn't respond
            summary = await client.chat.completions.create(model=m, messages=[
                {"role": "system", "content": summary_sysins},
                {"role": "user", "content": f"""
Previous memory:
{memory}

New messages:
{memory_context}

Update Kaelum's memory summary.
"""}],
                    temperature=1.5)
            memory = summary.choices[0].message.content.strip()
            print(memory)
            #save new memory
            metadata["san_diego_summary"] = memory
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
                        contents=f"context: {memory_context} \nKaelum: ",
                        config=norm_config,
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
                            {"role": "system", "content": san_diego_sysins},
                            {"role": "user", "content": f"""
Conversation summary:
{memory}

Recent messages:
{immediate_context}

What would Kaelum say next?
"""}
                        ],
                        temperature=1.5,
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

async def depressed_response(memory_context, immediate_context, personality="normal"):
    async with aiofiles.open(file_path, mode='r') as f:
        contents = await f.read()
        metadata = json.loads(contents)
    memory = metadata.get("depressed_summary") or metadata.get("summary") or ""
    #handle metadata for Kaelum
    for m in groq_queue:
        can_go = None
        try:
            #decide whether kaleum responds
            can_go = await client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": filter_prompt},
                    {"role": "user", "content": f"""
Previous memory:
{memory}

New messages:
{memory_context}

Should Kaelum respond?
"""}
                ],
                 temperature=0.1,
                 max_tokens=3
            )
            #handle memory and recursive summarization, always update his memory even if he doesn't respond
            summary = await client.chat.completions.create(model=m, messages=[
                {"role": "system", "content": summary_sysins},
                {"role": "user", "content": f"""
Previous memory:
{memory}

New messages:
{memory_context}

Update Kaelum's memory summary.
"""}],
                    temperature=1.5)
            memory = summary.choices[0].message.content.strip()
            print(memory)
            #save new memory
            metadata["depressed_summary"] = memory
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
                        contents=f"context: {memory_context} \nKaelum: ",
                        config=norm_config,
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
                            {"role": "system", "content": depressed_sysins},
                            {"role": "user", "content": f"""
Conversation summary:
{memory}

Recent messages:
{immediate_context}

What would Kaelum say next?
"""}
                        ],
                        temperature=1.5,
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
