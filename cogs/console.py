import discord
from discord.ext import commands
import readline
from cogs.constant import admins
import os

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
            await interaction.response.send_message(" ".join(history), ephemeral=True)
        else:
            await interaction.response.send_message("no perms ask bot dev zzz", ephemeral=True)

    @discord.app_commands.command(name="execute", description="Execute a command in console")
    async def execute(self, interaction: discord.Interaction, command: str):
        if interaction.user.id in self.admins:
            os.system(command)
            await interaction.response.send_message(f'Executed "{command}" in terminal', ephemeral=True)

async def setup(client):
    await client.add_cog(Console(client))
