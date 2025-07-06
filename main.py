import os
import time
import random
import asyncio
import discord
from datetime import timedelta
from dotenv import load_dotenv
from discord.ext import commands
from keep_alive import keep_alive

keep_alive()  # pour Render

# ─────────────── CONFIGURATION ───────────────
load_dotenv()
TOKEN = os.getenv("TOKEN")
PARTENARIAT_CHANNEL_ID = 1312467445881114635
BOT_WHITELIST = []

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─────────────── ANTI-SPAM ───────────────
user_message_count = {}
spam_threshold = 5
interval = 5

# ─────────────── EVENTS ───────────────
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")

@bot.event
async def on_member_join(member):
    if member.bot and member.id not in BOT_WHITELIST:
        try:
            await member.kick(reason="Bot non-whitelisté")
        except Exception as e:
            print(f"[kick bot] {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = asyncio.get_event_loop().time()
    user_message_count.setdefault(uid, []).append(now)
    user_message_count[uid] = [t for t in user_message_count[uid] if now - t < interval]

    if len(user_message_count[uid]) > spam_threshold:
        try:
            await message.author.timeout(timedelta(seconds=60), reason="Spam")
            embed = discord.Embed(
                description=f"🚫 {message.author.mention} a été mute 60s pour spam.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
        except Exception as e:
            print(f"[timeout] {e}")

    if ("discord.gg" in message.content or "discord.com/invite" in message.content) and message.channel.id != PARTENARIAT_CHANNEL_ID:
        try:
            await message.delete()
            embed = discord.Embed(
                description=f"🔗 {message.author.mention} : les liens Discord sont interdits ici.",
                color=discord.Color.orange()
            )
            await message.channel.send(embed=embed)
        except Exception as e:
            print(f"[delete link] {e}")

    await bot.process_commands(message)

# ─────────────── COMMANDES MODÉRATION ───────────────
@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    for ch in ctx.guild.text_channels:
        await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        description="🔒 Tous les salons texte ont été verrouillés.",
        color=discord.Color.dark_gray()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    for ch in ctx.guild.text_channels:
        await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(
        description="🔓 Tous les salons texte ont été déverrouillés.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, membre: discord.Member, *, reason=""):
    await membre.ban(reason=reason)
    embed = discord.Embed(
        title="🔨 Bannissement",
        description=f"{membre.mention} a été banni.\n**Raison :** {reason}",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Banni par {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, membre: discord.Member, *, reason=""):
    await membre.kick(reason=reason)
    embed = discord.Embed(
        title="👢 Expulsion",
        description=f"{membre.mention} a été expulsé.\n**Raison :** {reason}",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Kické par {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, nombre: int):
    deleted = await ctx.channel.purge(limit=nombre + 1)
    embed = discord.Embed(
        description=f"🧹 {len(deleted)-1} messages supprimés.",
        color=discord.Color.dark_gold()
    )
    await ctx.send(embed=embed, delete_after=3)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear_user(ctx, membre: discord.Member, nombre: int = 10):
    def check(m): return m.author == membre
    deleted = await ctx.channel.purge(limit=100, check=check)
    embed = discord.Embed(
        description=f"🧹 {len(deleted)} messages supprimés de {membre.mention}.",
        color=discord.Color.dark_gold()
    )
    await ctx.send(embed=embed, delete_after=3)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, membre: discord.Member, duree: int = 300):
    await membre.timeout(timedelta(seconds=duree), reason=f"mute {ctx.author}")
    embed = discord.Embed(
        description=f"🔇 {membre.mention} a été mute pour {duree} secondes.",
        color=discord.Color.greyple()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, membre: discord.Member):
    await membre.timeout(None, reason=f"unmute {ctx.author}")
    embed = discord.Embed(
        description=f"🔊 {membre.mention} a été unmute.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# ─────────────── COMMANDES FUN ───────────────
ROASTS = [
    "frérot t’es éclaté au sol, même en rêve tu rates tes combos.",
    "on dirait que t’as été nerfé à la naissance.",
    "tu joues comme si t’avais des moufles sur le clavier.",
    "même les bots ont pitié quand ils te voient jouer.",
    "ta présence baisse le MMR de tout le serveur."
]

@bot.command()
async def insulte(ctx, membre: discord.Member):
    embed = discord.Embed(
        description=f"{membre.mention}, {random.choice(ROASTS)}",
        color=discord.Color.magenta()
    )
    await ctx.send(embed=embed)

@bot.command()
async def insulte_random(ctx):
    humains = [m for m in ctx.guild.members if not m.bot and m != ctx.author]
    if not humains:
        return await ctx.send("Personne à insulter 😅")
    cible = random.choice(humains)
    embed = discord.Embed(
        description=f"{cible.mention}, {random.choice(ROASTS)}",
        color=discord.Color.magenta()
    )
    await ctx.send(embed=embed)

@bot.command()
async def cat(ctx):
    embed = discord.Embed(
        title="😺 Chat sacré",
        description="Un chat si expressif...",
        color=discord.Color.orange()
    )
    embed.set_image(url="https://media.tenor.com/Bg3ShfbkKJwAAAAC/rigby-cat-rigby.gif")
    await ctx.send(embed=embed)

# ─────────────── HELP ───────────────
@bot.command(name="help")
async def help_command(ctx):
    e = discord.Embed(title="🛡️ Commandes du bot", color=discord.Color.blue())
    e.add_field(name="🔒 !lockdown / 🔓 !unlock", value="Verrouille / déverrouille les salons", inline=False)
    e.add_field(name="🔨 !ban / 👢 !kick", value="Bannir / expulser un membre", inline=False)
    e.add_field(name="🔇 !mute / 🔊 !unmute", value="Timeout (mute) ou unmute un membre", inline=False)
    e.add_field(name="🧹 !clear <n>", value="Supprimer n messages", inline=False)
    e.add_field(name="🧹 !clear_user @membre", value="Supprimer messages d'un membre", inline=False)
    e.add_field(name="🤬 !insulte @membre", value="Envoie une insulte fun", inline=False)
    e.add_field(name="🎯 !insulte_random", value="Roast un membre au hasard", inline=False)
    e.add_field(name="🐈 !cat", value="Affiche un chat rigolo", inline=False)
    await ctx.send(embed=e)

# ─────────────── LANCEMENT ───────────────
while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[CRASH] {e}\nRedémarrage dans 5s...")
        time.sleep(5)
