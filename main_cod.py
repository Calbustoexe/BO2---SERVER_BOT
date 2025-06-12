import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio

# === Mini serveur HTTP pour Render ===
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_keep_alive():
    server = HTTPServer(("0.0.0.0", 8080), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_keep_alive, daemon=True).start()

# === Discord bot ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!!", intents=intents)

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Cog chargé : {filename}")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Call Of Duty: Black Ops II"))
    print(f"Connecté en tant que {bot.user.name}")

    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur de sync : {e}")

async def main():
    await load_cogs()  # Charge les cogs AVANT de démarrer le bot
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())