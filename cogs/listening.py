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
from ai.ai import generate_response, annoying_response # import ai logic
class ChannelSelectView(discord.ui.View):
    def __init__(self, listening_channels):
        super().__init__(timeout=60)
        self.listening_channels = listening_channels
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select a channel...",
        min_values=1,
        max_values=1,
        channel_types=[discord.ChannelType.text]
    )
    async def select_callback(self, interaction: discord.Interaction, select: ChannelSelect):
        if interaction.user.id in [1217433559564947561, 1399422471580680333]:
            id = select.values[0].id
            if id in list(self.listening_channels.keys()):
                old = self.listening_channels[id]
                if old == generate_response:
                    self.listening_channels[id] = annoying_response
                else:
                    self.listening_channels[id] = generate_response
                await interaction.response.send_message(f"Successfully switched personality from {old.__name__} to {self.listening_channels[id].__name__}", ephemeral=True)
            else:
                await interaction.response.send_message("Channel is not being listened on!", ephemeral=True)

        else:
            await interaction.response.send_message("no perms bozo", ephemeral=True)

class Listen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listening_channels = {
            1469061074744774860: generate_response,
            1348353795666477090: generate_response,
            1305221609539244090: generate_response,
            1360298343762362368: generate_response
        }

    # When a message is sent in any of the listening channels, check the previous 7 messages in that channel for context and convert it to json

    @commands.Cog.listener()
    async def on_message(self, message):
        print("processing message")
        if "k.echo" in message.content and message.author.id in [1217433559564947561, 1399422471580680333]:
            await message.channel.send(message.content.split("k.echo")[1])
        else:
            if message.channel.id in self.listening_channels and not message.author.bot:
                messages = [msg async for msg in message.channel.history(limit=15)]
                memory_context = "\n".join(f"{m.author.name}: {m.content}" for m in messages if m.content)
                immediate_context = "\n".join(f"{m.author.name}: {m.content}" for m in messages[10:] if m.content)

                try:
                    async with message.channel.typing():

                        response = await self.listening_channels[message.channel.id](memory_context, immediate_context)# Generate the response
                        if response:
                            redacted_response = response.replace("@here", "[REDACTED MASS PING]")
                            redacted_response2 = redacted_response.replace("@everyone", "[REDACTED MASS PING]")
                        else:
                            redacted_response = None
                            redacted_response2 = None

                except Exception as e:
                    await message.channel.send(f"AI ERROR: {e}")
                if redacted_response2:
                    await message.channel.send(redacted_response2)
                elif redacted_response:
                    await message.channel.send(redacted_response)
                elif response:
                    await message.channel.send(response)

            await self.bot.process_commands(message)

    @discord.app_commands.command(name="switch", description="Switches the personality of Kaelum from normal to annoying, or vice versa in specific channels.")
    async def switch(self, interaction: discord.Interaction):
        view = ChannelSelectView(self.listening_channels)
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.app_commands.command(name="listen", description="Begins listening in the current channel.")
    async def listen(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        if channel_id in self.listening_channels:
            await interaction.response.send_message("Already listening in current channel!", ephemeral=True)
        else:
            self.listening_channels[channel_id] = generate_response
            await interaction.response.send_message(f"Began listening in #{interaction.channel.name}.", ephemeral=True)

    @discord.app_commands.command(name="purge", description="Stops listening in the current channel.")
    async def purge(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        if channel_id not in self.listening_channels:
            await interaction.response.send_message("Not already listening in current channel!", ephemeral=True)
        else:
            del self.listening_channels[channel_id]
            await interaction.response.send_message(f"Stopped listening in #{interaction.channel.name}.", ephemeral=True)


async def setup(client):
    await client.add_cog(Listen(client))
