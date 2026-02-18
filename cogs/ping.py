import discord
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="ping", description="Makes sure bot is actually running")
    async def spawn(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

async def setup(client):
    await client.add_cog(Ping(client))