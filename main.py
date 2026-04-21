import os
import time
import random
import asyncio
import discord
import aiohttp
from datetime import timedelta
from dotenv import load_dotenv
from discord.ext import commands
from keep_alive import keep_alive

keep_alive()

load_dotenv()
TOKEN = os.getenv("TOKEN")
PARTENARIAT_CHANNEL_ID = 1312467445881114635

DISBOARD_ID = 302050872383242240
MAKEITAQUOTE_ID = 949479338275913799
FLAVIBOT_ID = 684773505157431347
VANITY_ID = 1457014404158853192

BOT_WHITELIST = {
    DISBOARD_ID,
    MAKEITAQUOTE_ID,
    FLAVIBOT_ID,
    VANITY_ID
}

BLACKLIST_USERS = set()
WARN_COUNTS = {}

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

user_message_count = {}
spam_threshold = 5
interval = 5

# ================= EVENTS =================

@bot.event
async def on_member_join(member):
    if member.id in BLACKLIST_USERS:
        await member.kick(reason="Blacklist")
        return

    if member.bot and member.id not in BOT_WHITELIST:
        await member.kick(reason="Bot non autorisé")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = asyncio.get_event_loop().time()
    user_message_count.setdefault(uid, []).append(now)
    user_message_count[uid] = [t for t in user_message_count[uid] if now - t < interval]

    if len(user_message_count[uid]) > spam_threshold:
        await message.author.timeout(timedelta(seconds=60), reason="Spam")

    await bot.process_commands(message)

# ================= COMMANDES =================

@bot.command()
async def insulte(ctx, membre: discord.Member):
    roasts = ["Skill issue.", "T’es éclaté au sol.", "Même les bots jouent mieux."]
    await ctx.send(f"{membre.mention}, {random.choice(roasts)}")


# ================= SHAME =================

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def shame(ctx):
    if not ctx.message.reference:
        return await ctx.send("❌ Répond à un message.")

    try:
        ref = ctx.message.reference
        msg = ref.resolved or await ctx.channel.fetch_message(ref.message_id)

        embed = discord.Embed(
            title="📢 SHAME",
            description=f"💀 {msg.author.mention} a dit :\n```{msg.content or '...'} ```",
            color=discord.Color.red()
        )

        await ctx.send(content="@here", embed=embed)

    except Exception as e:
        await ctx.send(f"Erreur: {e}")


@shame.error
async def shame_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Attends {round(error.retry_after,1)}s")


# ================= FEMBOY =================

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def femboy(ctx):
    try:
        url = "https://femboyfinder.firestreaker2.gg/api/femboy"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:

                if response.status != 200:
                    return await ctx.send("❌ API error")

                data = await response.json()

        image = data.get("url")

        embed = discord.Embed(
            title="💖 Femboy",
            color=discord.Color.pink()
        )
        embed.set_image(url=image)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send("❌ Erreur API")
        print(e)


# ================= READY =================

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    await bot.change_presence(activity=discord.Game("Bot actif"))

# ================= RUN =================

while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print("Crash:", e)
        time.sleep(5)
