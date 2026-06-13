import discord
from discord.ext import commands
import readline
from cogs.constant import admins

class Console(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admins = admins

    @discord.app_commands.command(name="console", description="Shows console history (I hope)")
    async def spawn(self, interaction: discord.Interaction):
        if interaction.user.id in self.admins:
            history = []
            for i in range(1, readline.get_current_history_length() + 1):
                history.append(readline.get_history_item(i))
            await interaction.response.send_message(" ".join(history))
        else:
            await interaction.response.send_message("no perms ask bot dev zzz")

async def setup(client):
    await client.add_cog(Console(client))
