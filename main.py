
# main.py
import os
import discord
from discord.ext import commands
import threading


class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = commands.when_mentioned_or("!"),
            intents = discord.Intents.all(),
            help_command = commands.DefaultHelpCommand(dm_help=True)
        )

    async def setup_hook(self): #overwriting a handler
        cogs_folder = f"{os.path.abspath(os.path.dirname(__file__))}/cogs"
        for filename in os.listdir(cogs_folder):
            print(filename)
            if filename.endswith(".py"):
                await client.load_extension(f"cogs.{filename[:-3]}")
        await client.tree.sync()
        print("Loaded cogs")
client = Client()
client.run(os.environ['DISCORD_TOKEN'])