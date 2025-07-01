import os
import time
import random
import asyncio
import discord
from datetime import timedelta, datetime
from dotenv import load_dotenv
from discord.ext import commands
from keep_alive import keep_alive
keep_alive()

# CONFIGURATION
load_dotenv()
TOKEN = os.getenv("TOKEN")
PARTENARIAT_CHANNEL_ID = 1312467445881114635
BOT_WHITELIST = []
VERIFY_MESSAGE_ID = 1389351508163694795
NON_VERIF_ROLE_NAME = "Non vérifié"

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")

# LANCEMENT
while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[CRASH] {e}\nRedémarrage dans 5s...")
        time.sleep(5)
