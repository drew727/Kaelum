import logging
import asyncio
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
import discord
from discord.ext import commands
import discord.ui
from discord.ui import ChannelSelect, View
from ai.ai import generate_response # import ai logic

class ChannelSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select a channel...",
        min_values=1,
        max_values=1,
        channel_types=[discord.ChannelType.text]
    )
    async def select_callback(self, interaction: discord.Interaction, select: ChannelSelect):
        if interaction.user.id in [1217433559564947561, 1399422471580680333]:
            id = int(select.values[0])
            if id in list(self.listening_channels.keys()):
                old = self.listening_channels[id]
                if old == "normal":
                    self.listening_channels[id] = "annoying"
                else:
                    self.listening_channels[id] = "normal"
                await interaction.response.send_message(f"Successfully switched personality from {old} to {self.listening_channels[id]}", ephemeral=True)
            else:
                await interaction.response.send_message("Channel is not being listened on!", ephemeral=True)

        else:
            await interaction.response.send_message("no perms bozo", ephemeral=True)

class Listen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listening_channels = {
            1469061074744774860: "normal",
            1348353795666477090: "normal",
            1305221609539244090: "normal",
            1360298343762362368: "normal"
        }

    # When a message is sent in any of the listening channels, check the previous 7 messages in that channel for context and convert it to json

    @commands.Cog.listener()
    async def on_message(self, message):
        print("processing message")
        if message.channel.id in self.listening_channels and not message.author.bot:
            messages = [msg async for msg in message.channel.history(limit=7)]
            context = "\n".join(f"{msg.author.name}: {msg.content}" for msg in reversed(messages) if msg.content)

            try:
                async with message.channel.typing():

                    response = await generate_response(context, self.listening_channels[message.channel.id]) # Generate the response
            except Exception as e:
                await message.channel.send(f"AI ERROR: {e}")
            if response:
                await message.channel.send(response)

        await self.bot.process_commands(message)

    @discord.app_commands.command(name="switch", description="Switches the personality of Kaelum from normal to annoying, or vice versa in specific channels.")
    async def switch(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=ChannelSelectView(), ephemeral=True)

async def setup(client):
    await client.add_cog(Listen(client))
