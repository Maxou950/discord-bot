import os
import time
import random
import asyncio
import discord
from datetime import timedelta
from dotenv import load_dotenv
from discord.ext import commands
from keep_alive import keep_alive

keep_alive()

# ─────────────── CONFIGURATION ───────────────
load_dotenv()
TOKEN = os.getenv("TOKEN")
PARTENARIAT_CHANNEL_ID = 1312467445881114635

# ✅ Utiliser des Entiers, pas des strings
DISBOARD_ID = 302050872383242240
MAKEITAQUOTE_ID = 949479338275913799
FLAVIBOT_ID = 684773505157431347
BOT_WHITELIST = {
    DISBOARD_ID,
    MAKEITAQUOTE_ID,
    FLAVIBOT_ID
}  # set d'ints, plus efficace pour les recherches

# 🚫 Utilisateurs blacklistés (empêchés de rejoindre : kick auto)
BLACKLIST_USERS = {
    #1175143594919731291,
}

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
    # Petit log pour vérifier l'ID du membre qui rejoint
    try:
        print(f"[DEBUG] Join: {member} | id={member.id} | bot={member.bot}")
    except Exception:
        pass

    # ─────────────── BLACKLIST UTILISATEURS (anti-join) ───────────────
    if member.id in BLACKLIST_USERS:
        try:
            await member.kick(reason="Utilisateur blacklisté (anti-join)")
            print(f"[BLACKLIST] {member} expulsé (blacklist join)")
            return
        except Exception as e:
            print(f"[blacklist kick error] {e}")

    # ─────────────── GESTION DES BOTS ───────────────
    if member.bot and member.id not in BOT_WHITELIST:
        try:
            await member.kick(reason="Bot non-whitelisté")
            print(f"[INFO] Bot {member} expulsé (non whitelisté)")
        except Exception as e:
            print(f"[kick bot] {e}")
    elif member.bot:
        print(f"[INFO] Bot whitelisté autorisé: {member} (id={member.id})")

@bot.event
async def on_message(message):
    # Si on veut ignorer totalement les messages d'utilisateurs blacklistés (optionnel)
    # if message.author.id in BLACKLIST_USERS:
    #     return

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

# ─────────────── COMMANDES GESTION BLACKLIST (ANTI-JOIN) ───────────────
@bot.command()
@commands.has_permissions(administrator=True)
async def add_blacklist(ctx, membre: discord.Member):
    BLACKLIST_USERS.add(membre.id)
    await ctx.send(f"🚫 {membre.mention} a été **ajouté** à la blacklist (anti-join).")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_blacklist(ctx, membre: discord.Member):
    BLACKLIST_USERS.discard(membre.id)
    await ctx.send(f"✅ {membre.mention} a été **retiré** de la blacklist (anti-join).")

@bot.command()
@commands.has_permissions(administrator=True)
async def show_blacklist(ctx):
    if not BLACKLIST_USERS:
        return await ctx.send("✅ La blacklist (anti-join) est **vide**.")
    noms = [f"<@{uid}>" for uid in BLACKLIST_USERS]
    await ctx.send("🚫 **Blacklist (anti-join) :**\n" + "\n".join(noms))

# ─────────────── COMMANDES FUN ───────────────
ROASTS = [
    "Skillisue.",
    "Tu fais peur à voir bro.",
    "tu joues comme si t’avais des moufles sur le clavier.",
    "même les bots ont pitié quand ils te voient jouer.",
    "Trickshot dans ton père sah.",
    "arrache ta tante.",
    "Va niquer ta mère toi et la roue",
    "Mimi va niquer ta mère sale tana",
    "On préfère mimi à toi (c'est quelque chose sah)"
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

@bot.command()
async def skillissue(ctx):
    embed = discord.Embed(
        title="💢 Skill Issue",
        description="Un manque de compétence détecté...",
        color=discord.Color.red()
    )

    file = discord.File("image4.png", filename="image4.png")
    embed.set_image(url="attachment://image4.png")

    # Envoi dans un seul message
    await ctx.send(embed=embed, file=file)
    
@bot.command()
@commands.has_permissions(administrator=True)
async def roulette(ctx, *membres: discord.Member):
    """Ban Gambling : mute aléatoirement un des joueurs pendant 10 minutes."""

    # Vérif de base : au moins 2 joueurs
    if len(membres) < 2:
        return await ctx.send(
            "❌ Il faut au moins **2 joueurs mentionnés** pour lancer une roulette russe.\n"
            "Ex : `!roulette @joueur1 @joueur2 @joueur3`"
        )

    # On enlève les bots de la liste
    participants = [m for m in membres if not m.bot]

    if len(participants) < 2:
        return await ctx.send("❌ Les bots ne jouent pas. Mentionne au moins **2 humains**.")

    # On choisit le perdant
    perdant = random.choice(participants)

    try:
        # Mute 10 minutes
        await perdant.timeout(
            timedelta(minutes=10),
            reason=f"Perdant à la roulette russe (par {ctx.author})"
        )
    except discord.errors.HTTPException as e:
        # Cas Discord qui renvoie une "erreur" vide alors que c'est bien appliqué
        if e.status == 204:
            pass  # Pas grave, le mute est appliqué quand même
        else:
            print(f"[roulette timeout] {e}")
            return await ctx.send(
                f"⚠️ Impossible de mute {perdant.mention}. Vérifie mes permissions."
            )
    except Exception as e:
        print(f"[roulette timeout] {e}")
        return await ctx.send(
            f"⚠️ Erreur inattendue pendant le mute : {e}"
        )

    # Embed de résultat
    embed = discord.Embed(
        title="🔫 Roulette russe",
        description=(
            "Participants : " + ", ".join(m.mention for m in participants) + "\n\n"
            f"💥 **Perdant : {perdant.mention}**\n"
            "Il est mute pendant **10 minutes**."
        ),
        color=discord.Color.dark_red()
    )
    embed.set_footer(
        text=f"Lancée par {ctx.author}",
        icon_url=getattr(ctx.author.avatar, 'url', discord.Embed.Empty)
    )

    await ctx.send(embed=embed)

    # Message clair dans le salon
    await ctx.send(
        f"💥 {perdant.mention} a perdu la roulette russe ! "
        "Il est réduit au silence pendant 10 minutes 😈"
    )

@bot.command(name="Nahidwin")
async def nahidwin(ctx):
    folder = "images"  # dossier dans ton repo
    # On récupère tous les fichiers image du dossier
    try:
        fichiers = [
            f for f in os.listdir(folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        ]
    except FileNotFoundError:
        return await ctx.send("❌ Dossier `images` introuvable, vérifie qu'il est bien à la racine du projet.")

    if not fichiers:
        return await ctx.send("❌ Il n'y a aucune image dans le dossier `images`.")

    # On choisit une image au hasard
    fichier_choisi = random.choice(fichiers)
    chemin_complet = os.path.join(folder, fichier_choisi)

    # Prépare le fichier et l'embed
    file = discord.File(chemin_complet, filename=fichier_choisi)

    embed = discord.Embed(
        title="Nah I'd win",
        description="Quel Gojo on a aujourd'hui ?",
        color=discord.Color.purple()
    )
    embed.set_image(url=f"attachment://{fichier_choisi}")

    await ctx.send(embed=embed, file=file)

static void UpdatePresence()
{
    DiscordRichPresence discordPresence;
    memset(&discordPresence, 0, sizeof(discordPresence));
    discordPresence.state = "Jerkmate";
    discordPresence.details = "Ranked";
    discordPresence.startTimestamp = 1507665886;
    discordPresence.endTimestamp = 1507665886;
    discordPresence.largeImageKey = "f4ppzsdwsaa29nj";
    discordPresence.smallImageText = "Rogue - Level 100";
    discordPresence.partyId = "ae488379-351d-4a4f-ad32-2b9b01c91657";
    discordPresence.partySize = 2;
    discordPresence.partyMax = 4;
    discordPresence.joinSecret = "MTI4NzM0OjFpMmhuZToxMjMxMjM= ";
    Discord_UpdatePresence(&discordPresence);
}
    
# ─────────────── HELP ───────────────
@bot.command(name="help")
async def help_command(ctx):
    e = discord.Embed(title="🛡️ Commandes du bot", color=discord.Color.blue())
    e.add_field(name="🔒 !lockdown / 🔓 !unlock", value="Verrouille / déverrouille les salons", inline=False)
    e.add_field(name="🔨 !ban / 👢 !kick", value="Bannir / expulser un membre", inline=False)
    e.add_field(name="🔇 !mute / 🔊 !unmute", value="Timeout (mute) ou unmute un membre", inline=False)
    e.add_field(name="🧹 !clear <n>", value="Supprimer n messages", inline=False)
    e.add_field(name="🧹 !clear_user @membre", value="Supprimer messages d'un membre", inline=False)
    e.add_field(name="🚫 Blacklist (anti-join)", value="!add_blacklist @membre | !remove_blacklist @membre | !show_blacklist", inline=False)
    e.add_field(name="🤬 !insulte @membre", value="Envoie une insulte fun", inline=False)
    e.add_field(name="🎯 !insulte_random", value="Roast un membre au hasard", inline=False)
    e.add_field(name="🐈 !cat / 💢 !skillissue", value="Fun/Images", inline=False)
    await ctx.send(embed=e)

# ─────────────── LANCEMENT ───────────────
while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[CRASH] {e}\nRedémarrage dans 5s...")
        time.sleep(5)
