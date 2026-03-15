import os
import discord
from discord.ext import commands
import threading
import json # Added import
from http.server import HTTPServer, BaseHTTPRequestHandler

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = commands.when_mentioned_or("%"),
            intents = discord.Intents.all(),
            help_command = commands.DefaultHelpCommand(dm_help=True)
        )

    async def setup_hook(self): #overwriting a handler
        cogs_folder = f"{os.path.abspath(os.path.dirname(__file__))}/cogs"
        for filename in os.listdir(cogs_folder):
            print(filename)
            if filename.endswith(".py") and filename != "ping.py":
                await client.load_extension(f"cogs.{filename[:-3]}")
        await client.tree.sync()
        print("Loaded cogs")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        # Modified to load summary from the JSON file so we can debug memory
        with open("ai/kaelum_memory.json", "r") as f:
            data = json.load(f)
        self.wfile.write(data["summary"].encode())

def run_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

client = Client()

threading.Thread(target=run_server, daemon=True).start()
client.run(os.environ['DISCORD_TOKEN'])
