import discord
from discord.ext import commands
import readline

class Console(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="console", description="Shows console history (I hope)")
    async def spawn(self, interaction: discord.Interaction):
        history = []
        for i in range(1, readline.get_current_history_length() + 1):
            history.append(readline.get_history_item(i))
        await interaction.response.send_message(" ".join(history))

async def setup(client):
    await client.add_cog(Console(client))
