import logging

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
        self.listening_channels = [1469061074744774860] #channel id for 'ai-chat'

    # When a message is sent in any of the listening channels, check the previous 10 messages in that channel for context and convert it to json
    '''
    @commands.Cog.listener()
    async def on_message(self, message):
        print("processing message")
        if message.channel.id in self.listening_channels and not message.author.bot:
            messages = [msg async for msg in message.channel.history(limit=10)]
            context = []
            for msg in reversed(messages):
                context.append({
                    "author": msg.author.name,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
            response = await generate_response(context)  # Generate the response
            await message.channel.send(response)
            print(context)
            await message.chamnel.send("testing")
        await self.bot.process_commands(message)'''
async def setup(client):
    await client.add_cog(Listen(client))
