import logging
import asyncio
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
import discord
from discord.ext import commands
from ai.ai import generate_response # import ai logic
class Listen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listening_channels = [1469061074744774860, 1348353795666477090] #channel id for 'ai-chat'

    # When a message is sent in any of the listening channels, check the previous 10 messages in that channel for context and convert it to json

    @commands.Cog.listener()
    async def on_message(self, message):
        print("processing message")
        if message.channel.id in self.listening_channels and not message.author.bot:
            messages = [msg async for msg in message.channel.history(limit=10)]
            context = "\n".join(f"{msg.created_at.isoformat()} {msg.author.name}: {msg.content}" for msg in reversed(messages) if msg.content)
            try:
                async with message.channel.typing():
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(None, generate_response, context)  # Generate the response
            except Exception as e:
                await message.channel.send(f"AI ERROR: {e}")
            if response:
                await message.channel.send(response)

        await self.bot.process_commands(message)
async def setup(client):
    await client.add_cog(Listen(client))
