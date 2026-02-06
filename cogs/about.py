
import discord
from discord.ext import commands

class About(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="about", description="About this bot")
    async def about(self, interaction: discord.Interaction):
        emb = discord.Embed(color=discord.Color.blue(), title="About this bot!", description="This bot was made by cosmic.shrimp and drew2772. The goal of this project was to train an artifical intelligence solely on human interaction for a more conversationally fluent bot.")
        await interaction.response.send_message(embed=emb)

async def setup(client):
    await client.add_cog(About(client))