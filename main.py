import os
import discord
from discord.ext import commands
import threading
import json # Added import
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "ai", "kaelum_memory.json")


class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = commands.when_mentioned_or("%"),
            intents = discord.Intents.all(),
            help_command = commands.DefaultHelpCommand(dm_help=True)
        )

    async def setup_hook(self): #overwriting a handler
        cogs_folder = os.path.join(BASE_DIR, "cogs")
        for filename in os.listdir(cogs_folder):
            print(filename)
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        await self.tree.sync()
        print("Loaded cogs")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        # Modified to load summary from the JSON file so we can debug memory
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
        self.wfile.write(data["summary"].encode())

def run_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


def main():
    client = Client()
    threading.Thread(target=run_server, daemon=True).start()
    client.run(os.environ['DISCORD_TOKEN'])


if __name__ == "__main__":
    main()
