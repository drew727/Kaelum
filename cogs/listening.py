
import discord
from discord.ext import commands
from ai.ai import generate_response # import ai logic
class Listen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listening_channels = [1469061074744774860] #channel id for 'ai-chat'

    # When a message is sent in any of the listening channels, check the previous 10 messages in that channel for context and convert it to json
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in self.listening_channels and not message.author.bot:
            messages = await message.channel.history(limit=10).flatten()
            context = []
            for msg in reversed(messages):
                context.append({
                    "author": msg.author.name,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
            response = await generate_response(context)  # Generate the response
            await message.channel.send(response)
async def setup(client):
    await client.add_cog(Listen(client))
