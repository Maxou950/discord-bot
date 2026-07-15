import os
import time
import random
import asyncio
import io
import textwrap
import re
import discord
import aiohttp
from typing import Optional
from datetime import timedelta
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive
from PIL import Image, ImageDraw, ImageFont

keep_alive()

load_dotenv()
TOKEN = os.getenv("TOKEN")
PARTENARIAT_CHANNEL_ID = 1312467445881114635
TEST_GUILD_ID = None  # ex: 1234567890123456789
FUN_ROLE_ID = 1526959966525587666  # Remplace par l'ID du rôle « Commandes Fun »

DISBOARD_ID = 302050872383242240
MAKEITAQUOTE_ID = 949479338275913799
FLAVIBOT_ID = 684773505157431347
JOHN_BOT = 958547309728256081
INVITE_LOGGER_ID = 499595256270946326
FLAVIBOT2_ID = 749248172756303913
RAIDPROTECT_ID = 466578580449525760

BOT_WHITELIST = {
    DISBOARD_ID,
    MAKEITAQUOTE_ID,
    FLAVIBOT_ID,
    JOHN_BOT,
    INVITE_LOGGER_ID,
    RAIDPROTECT_ID,
    FLAVIBOT2_ID
}

BLACKLIST_USERS = {
    # 1175143594919731291,
}

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

LAST_FEMBOY_IMAGES = []
MAX_FEMBOY_HISTORY = 80

LAST_FEMBOY_CHARACTERS = []
MAX_FEMBOY_CHARACTER_HISTORY = 12

FEMBOY_TAGS = [
    "trap",
    "trap solo",
    "otokonoko",
    "feminine_male"
]

FEMBOY_CHARACTER_TAGS = {
    "astolfo",
    "felix_argyle",
    "hideyoshi_kinoshita",
    "hideri_kanzaki",
    "saika_totsuka",
    "nagisa_shiota",
    "gasper_vladi",
    "rimuru_tempest"
}

LAST_UMA_IMAGES = []
MAX_UMA_HISTORY = 40

UMA_BASE_TAGS = "umamusume"

UMA_CHARACTER_TAGS = {
    "oguri": "oguri_cap_(umamusume)",
    "teio": "tokai_teio_(umamusume)",
    "mcqueen": "mejiro_mcqueen_(umamusume)",
    "goldship": "gold_ship_(umamusume)",
    "rice": "rice_shower_(umamusume)",
    "kita": "kitasan_black_(umamusume)",
    "satono": "satono_diamond_(umamusume)",
    "opera" : "t.m._opera_o_(umamusume)"
}

UMA_BLACKLIST = {
    "comic",
    "translated",
    "greyscale",
    "monochrome",
    "text",
    "speech_bubble",
    "4koma",
    "multiple_views",
    "chibi",
    "simple_background",
    "sketch",
    "lineart"
}

LAST_HOUSEKI_IMAGES = []
MAX_HOUSEKI_HISTORY = 40

HOUSEKI_BASE_TAGS = "houseki_no_kuni"

HOUSEKI_CHARACTER_TAGS = {
    "phos": "phosphophyllite_(houseki_no_kuni)",
    "cinnabar": "cinnabar_(houseki_no_kuni)",
    "diamond": "diamond_(houseki_no_kuni)",
    "bort": "bort_(houseki_no_kuni)",
    "rutile": "rutile_(houseki_no_kuni)",
    "antarcticite": "antarcticite_(houseki_no_kuni)",
    "padpa": "padparadscha_(houseki_no_kuni)",
    "ghost": "ghost_quartz_(houseki_no_kuni)",
    "euclase": "euclase_(houseki_no_kuni)"
}

HOUSEKI_BLACKLIST = {
    "comic",
    "translated",
    "greyscale",
    "monochrome",
    "text",
    "speech_bubble",
    "4koma",
    "multiple_views",
    "chibi",
    "simple_background",
    "sketch",
    "lineart"
}

ALLOWED_INVITE_USERS = {
    1278501132771000320,  # Krakotte
    504958077305487371,   # Maxou
}

ROASTS = [
    "Skillisue.",
    "Tu fais peur à voir bro.",
    "tu joues comme si t’avais des moufles sur le clavier.",
    "même les bots ont pitié quand ils te voient jouer.",
    "Trickshot dans ton père sah.",
    "arrache ta tante.",
    "Va niquer ta mère toi et la roue",
    "On préfère mimi à toi (c'est quelque chose sah)",
    "Sale juif",
    "Neck hurts",
    "Gemme pale et Noir"
]


def extract_recent_femboy_character(tag_string: str):
    tags = set(tag_string.split())
    found = tags & FEMBOY_CHARACTER_TAGS
    if found:
        return sorted(found)[0]
    return None


def fun_role_or_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False

        if interaction.user.guild_permissions.administrator:
            return True

        return any(role.id == FUN_ROLE_ID for role in interaction.user.roles)

    return app_commands.check(predicate)



# ---------------------------------------------------------------------------
# Configuration des boîtes de dialogue style Undertale / Deltarune
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIALOGUE_WIDTH = 760
DIALOGUE_MIN_HEIGHT = 220
DIALOGUE_MARGIN = 12
DIALOGUE_PORTRAIT_SIZE = 150

PORTRAIT_FOLDER = os.path.join(BASE_DIR, "assets", "portraits")

# Le code essaie d'abord deltarune.ttf, puis determination.ttf.
DIALOGUE_FONT_PATHS = [
    os.path.join(BASE_DIR, "assets", "fonts", "deltarune.ttf"),
    os.path.join(BASE_DIR, "assets", "fonts", "determination.ttf"),
]


def load_dialogue_font(size: int) -> ImageFont.ImageFont:
    """Charge la police du projet, puis une police de secours."""
    candidates = DIALOGUE_FONT_PATHS + [
        "DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]

    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


def find_portrait(personnage: Optional[str]) -> Optional[str]:
    """Trouve un portrait sans tenir compte des majuscules/minuscules."""
    if not personnage or not os.path.isdir(PORTRAIT_FOLDER):
        return None

    wanted_name = personnage.strip().lower()

    for filename in os.listdir(PORTRAIT_FOLDER):
        name, extension = os.path.splitext(filename)

        if extension.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            continue

        if name.lower() == wanted_name:
            return os.path.join(PORTRAIT_FOLDER, filename)

    return None


def wrap_dialogue_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int
) -> list[str]:
    """Découpe le texte selon sa largeur réelle dans l'image."""
    paragraphs = text.replace("\r", "").split("\n")
    result = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            result.append("")
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:
            candidate = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)

            if bbox[2] - bbox[0] <= max_width:
                current_line = candidate
                continue

            if current_line:
                result.append(current_line)

            bbox_word = draw.textbbox((0, 0), word, font=font)
            if bbox_word[2] - bbox_word[0] <= max_width:
                current_line = word
            else:
                chunks = textwrap.wrap(word, width=18) or [word]
                result.extend(chunks[:-1])
                current_line = chunks[-1]

        if current_line:
            result.append(current_line)

    return result or [""]


def create_dialogue_image(
    texte: str,
    personnage: Optional[str] = None,
    avatar_bytes: Optional[bytes] = None
) -> io.BytesIO:
    """
    Crée la boîte de dialogue.
    - personnage fourni : utilise son PNG dans assets/portraits ;
    - aucun personnage : utilise l'avatar Discord reçu dans avatar_bytes.
    """
    font = load_dialogue_font(34)

    portrait = None

    if personnage:
        portrait_path = find_portrait(personnage)
        if portrait_path is None:
            raise FileNotFoundError(
                f"Aucun portrait trouvé pour '{personnage}' dans assets/portraits."
            )
        portrait = Image.open(portrait_path).convert("RGBA")
    elif avatar_bytes:
        portrait = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

    # Il y a normalement toujours un portrait : PNG ou avatar Discord.
    has_portrait = portrait is not None
    text_x = 205 if has_portrait else 58
    text_max_width = DIALOGUE_WIDTH - text_x - 38

    temporary = Image.new("RGB", (DIALOGUE_WIDTH, DIALOGUE_MIN_HEIGHT), "black")
    temporary_draw = ImageDraw.Draw(temporary)
    lines = wrap_dialogue_text(temporary_draw, texte, font, text_max_width)

    line_height = 46
    content_height = max(
        DIALOGUE_MIN_HEIGHT,
        68 + len(lines) * line_height + 38
    )

    image = Image.new("RGB", (DIALOGUE_WIDTH, content_height), "black")
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (
            DIALOGUE_MARGIN,
            DIALOGUE_MARGIN,
            DIALOGUE_WIDTH - DIALOGUE_MARGIN - 1,
            content_height - DIALOGUE_MARGIN - 1,
        ),
        outline="white",
        width=6,
    )
    draw.rectangle(
        (
            DIALOGUE_MARGIN + 8,
            DIALOGUE_MARGIN + 8,
            DIALOGUE_WIDTH - DIALOGUE_MARGIN - 9,
            content_height - DIALOGUE_MARGIN - 9,
        ),
        outline="black",
        width=3,
    )

    if portrait is not None:
        # NEAREST garde le côté pixel art pour les PNG et pixelise aussi l'avatar.
        portrait.thumbnail(
            (DIALOGUE_PORTRAIT_SIZE, DIALOGUE_PORTRAIT_SIZE),
            Image.Resampling.NEAREST,
        )

        px = 38 + (DIALOGUE_PORTRAIT_SIZE - portrait.width) // 2
        py = (content_height - portrait.height) // 2
        image.paste(portrait, (px, py), portrait)

    y = 43
    for index, line in enumerate(lines):
        prefix = "* " if index == 0 else "  "
        draw.text((text_x, y), prefix + line, font=font, fill="white")
        y += line_height

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer



# ---------------------------------------------------------------------------
# Conversion automatique des liens sociaux pour les embeds Discord
# ---------------------------------------------------------------------------

SOCIAL_DOMAIN_REPLACEMENTS = {
    "twitter.com": "fxtwitter.com",
    "www.twitter.com": "fxtwitter.com",
    "mobile.twitter.com": "fxtwitter.com",
    "x.com": "fixupx.com",
    "www.x.com": "fixupx.com",
    "mobile.x.com": "fixupx.com",
    "tiktok.com": "vxtiktok.com",
    "www.tiktok.com": "vxtiktok.com",
    "m.tiktok.com": "vxtiktok.com",
    "vm.tiktok.com": "vxtiktok.com",
    "vt.tiktok.com": "vxtiktok.com",
    "instagram.com": "ddinstagram.com",
    "www.instagram.com": "ddinstagram.com",
    "bsky.app": "fxbsky.app",
    "www.bsky.app": "fxbsky.app",
}

SOCIAL_URL_PATTERN = re.compile(
    r"https?://[^\s<>]+",
    re.IGNORECASE
)


def convert_social_url(url: str) -> str:
    """Convertit un lien social vers un domaine qui génère un meilleur embed."""
    trailing_characters = ""

    while url and url[-1] in ".,;:!?)]}":
        trailing_characters = url[-1] + trailing_characters
        url = url[:-1]

    match = re.match(
        r"^(https?://)([^/]+)(/.*)?$",
        url,
        re.IGNORECASE
    )

    if not match:
        return url + trailing_characters

    protocol, domain, path = match.groups()
    replacement = SOCIAL_DOMAIN_REPLACEMENTS.get(domain.lower())

    if not replacement:
        return url + trailing_characters

    return f"{protocol}{replacement}{path or ''}{trailing_characters}"


def convert_social_links(content: str) -> tuple[str, bool]:
    """Convertit tous les liens sociaux présents dans un message."""
    converted_any_link = False

    def replace_url(match: re.Match) -> str:
        nonlocal converted_any_link

        original_url = match.group(0)
        converted_url = convert_social_url(original_url)

        if converted_url != original_url:
            converted_any_link = True

        return converted_url

    converted_content = SOCIAL_URL_PATTERN.sub(replace_url, content)
    return converted_content, converted_any_link


# ---------------------------------------------------------------------------
# Events (inchangés, ce ne sont pas des commandes)
# ---------------------------------------------------------------------------

@bot.event
async def on_member_join(member):
    try:
        print(f"[DEBUG] Join: {member} | id={member.id} | bot={member.bot}")
    except Exception:
        pass

    if member.id in BLACKLIST_USERS:
        try:
            await member.kick(reason="Utilisateur blacklisté (anti-join)")
            print(f"[BLACKLIST] {member} expulsé (blacklist join)")
            return
        except Exception as e:
            print(f"[blacklist kick error] {e}")

    if member.bot and member.id not in BOT_WHITELIST:
        try:
            await member.kick(reason="Bot non-whitelisté")
            print(f"[INFO] Bot {member} expulsé (non whitelisté)")
        except Exception as e:
            print(f"[kick bot] {e}")
    elif member.bot:
        print(f"[INFO] Bot whitelisté autorisé: {member} (id={member.id})")


@bot.event
async def on_message(message: discord.Message):
    # Ignore les messages des bots pour éviter les boucles.
    if message.author.bot:
        return

    # -----------------------------------------------------------------------
    # Anti-spam
    # -----------------------------------------------------------------------

    uid = message.author.id
    now = asyncio.get_running_loop().time()

    user_message_count.setdefault(uid, []).append(now)
    user_message_count[uid] = [
        timestamp
        for timestamp in user_message_count[uid]
        if now - timestamp < interval
    ]

    if len(user_message_count[uid]) > spam_threshold:
        try:
            await message.author.timeout(
                timedelta(seconds=60),
                reason="Spam"
            )

            embed = discord.Embed(
                description=f"🚫 {message.author.mention} a été mute 60s pour spam.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)

        except Exception as error:
            print(f"[timeout error] {error}")

    # -----------------------------------------------------------------------
    # Blocage des invitations Discord
    # -----------------------------------------------------------------------

    message_content_lower = message.content.lower()

    contains_discord_invite = (
        "discord.gg" in message_content_lower
        or "discord.com/invite" in message_content_lower
    )

    if (
        contains_discord_invite
        and message.channel.id != PARTENARIAT_CHANNEL_ID
        and message.author.id not in ALLOWED_INVITE_USERS
    ):
        try:
            await message.delete()

            embed = discord.Embed(
                description=(
                    f"🔗 {message.author.mention} : "
                    "les liens Discord sont interdits ici."
                ),
                color=discord.Color.orange()
            )
            await message.channel.send(embed=embed)

        except Exception as error:
            print(f"[delete invite error] {error}")

        return

    # -----------------------------------------------------------------------
    # Conversion des liens sociaux
    # -----------------------------------------------------------------------

    converted_content, converted_any_link = convert_social_links(
        message.content
    )

    if converted_any_link:
        try:
            await message.edit(suppress=True)

        except discord.Forbidden:
            print(
                "[social links] Permission « Gérer les messages » manquante : "
                "impossible de masquer l'embed original."
            )

        except discord.HTTPException as error:
            print(f"[social links suppress error] {error}")

        try:
            await message.reply(
                converted_content,
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none()
            )

        except discord.HTTPException as error:
            print(f"[social links reply error] {error}")


# ---------------------------------------------------------------------------
# Gestion d'erreur globale pour les slash commands
# (remplace les anciens décorateurs @command.error au cas par cas)
# ---------------------------------------------------------------------------

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        msg = f"⏳ Doucement... réessaie dans {round(error.retry_after, 1)}s."
    elif isinstance(error, app_commands.MissingPermissions):
        msg = "❌ Tu n'as pas la permission d'utiliser cette commande."
    elif isinstance(error, app_commands.CheckFailure):
        msg = "❌ Tu dois avoir le rôle **Commandes Fun** pour utiliser cette commande."
    else:
        print(f"[app command error] {type(error).__name__}: {error}")
        msg = f"❌ Erreur : {error}"

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception as e:
        print(f"[error handler send failed] {e}")


# ---------------------------------------------------------------------------
# Modération
# ---------------------------------------------------------------------------

@bot.tree.command(name="unwarn", description="Retirer 1 warn à un membre.")
@app_commands.describe(membre="Le membre à qui retirer un warn")
@app_commands.checks.has_permissions(moderate_members=True)
async def unwarn(interaction: discord.Interaction, membre: discord.Member):
    user_id = membre.id

    if user_id not in WARN_COUNTS or WARN_COUNTS[user_id] == 0:
        return await interaction.response.send_message(
            embed=discord.Embed(
                description=f"ℹ️ {membre.mention} n'a **aucun warn**.",
                color=discord.Color.blue()
            )
        )

    WARN_COUNTS[user_id] -= 1

    embed = discord.Embed(
        title="♻️ Warn retiré",
        description=(
            f"Un avertissement a été retiré à {membre.mention}.\n"
            f"**Warns restants :** {WARN_COUNTS[user_id]}/3"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(
        text=f"Action par {interaction.user}",
        icon_url=getattr(interaction.user.avatar, "url", None)
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="warn", description="Avertir un membre. À 3 warns, il est kick.")
@app_commands.describe(membre="Le membre à avertir", raison="La raison de l'avertissement")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie."):
    if membre.bot:
        return await interaction.response.send_message("❌ Tu ne peux pas warn un bot.", ephemeral=True)
    if membre == interaction.user:
        return await interaction.response.send_message("❌ Tu ne peux pas te warn toi-même.", ephemeral=True)
    if membre == interaction.guild.owner:
        return await interaction.response.send_message("❌ Tu ne peux pas warn le propriétaire du serveur.", ephemeral=True)

    user_id = membre.id
    WARN_COUNTS[user_id] = WARN_COUNTS.get(user_id, 0) + 1
    nb_warns = WARN_COUNTS[user_id]

    try:
        dm_embed = discord.Embed(
            title="⚠️ Avertissement",
            description=(
                f"Tu as reçu un avertissement sur le serveur **{interaction.guild.name}**.\n\n"
                f"**Modérateur :** {interaction.user} (`{interaction.user.id}`)\n"
                f"**Raison :** {raison}\n"
                f"**Nombre total de warns :** {nb_warns}/3"
            ),
            color=discord.Color.orange()
        )
        await membre.send(embed=dm_embed)
    except Exception:
        pass

    embed = discord.Embed(
        title="⚠️ Warn",
        description=(
            f"{membre.mention} a reçu un avertissement.\n"
            f"**Raison :** {raison}\n"
            f"**Warns :** {nb_warns}/3"
        ),
        color=discord.Color.orange()
    )
    embed.set_footer(
        text=f"Warn par {interaction.user}",
        icon_url=getattr(interaction.user.avatar, "url", None)
    )
    await interaction.response.send_message(embed=embed)

    if nb_warns >= 3:
        try:
            await membre.kick(reason=f"Atteint 3 warns (dernier warn par {interaction.user})")
            WARN_COUNTS.pop(user_id, None)

            kick_embed = discord.Embed(
                title="🔨 Auto-kick",
                description=f"{membre.mention} a été **kick** pour avoir atteint **3 avertissements**.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=kick_embed)
        except Exception as e:
            err_embed = discord.Embed(
                title="⚠️ Erreur kick",
                description=f"Impossible de kick {membre.mention}.\n```{e}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=err_embed)


@bot.tree.command(name="unlock", description="Déverrouille tous les salons texte du serveur.")
@app_commands.checks.has_permissions(administrator=True)
async def unlock(interaction: discord.Interaction):
    await interaction.response.defer()
    for ch in interaction.guild.text_channels:
        await ch.set_permissions(interaction.guild.default_role, send_messages=True)

    embed = discord.Embed(
        description="🔓 Tous les salons texte ont été déverrouillés.",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="ban", description="Bannir un membre.")
@app_commands.describe(membre="Le membre à bannir", raison="La raison du bannissement")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = ""):
    await membre.ban(reason=raison)
    embed = discord.Embed(
        title="🔨 Bannissement",
        description=f"{membre.mention} a été banni.\n**Raison :** {raison}",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Banni par {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="kick", description="Expulser un membre.")
@app_commands.describe(membre="Le membre à expulser", raison="La raison de l'expulsion")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = ""):
    await membre.kick(reason=raison)
    embed = discord.Embed(
        title="👢 Expulsion",
        description=f"{membre.mention} a été expulsé.\n**Raison :** {raison}",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Kické par {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Supprimer un nombre de messages dans le salon.")
@app_commands.describe(nombre="Le nombre de messages à supprimer")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, nombre: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=nombre)
    embed = discord.Embed(
        description=f"🧹 {len(deleted)} messages supprimés.",
        color=discord.Color.dark_gold()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="clear_user", description="Supprimer les messages d'un membre précis.")
@app_commands.describe(membre="Le membre dont on supprime les messages", nombre="Nombre de messages à parcourir")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_user(interaction: discord.Interaction, membre: discord.Member, nombre: int = 10):
    await interaction.response.defer(ephemeral=True)

    def check(m):
        return m.author == membre

    deleted = await interaction.channel.purge(limit=100, check=check)
    embed = discord.Embed(
        description=f"🧹 {len(deleted)} messages supprimés de {membre.mention}.",
        color=discord.Color.dark_gold()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="mute", description="Mute (timeout) un membre.")
@app_commands.describe(membre="Le membre à mute", duree="Durée du mute en secondes")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membre: discord.Member, duree: int = 300):
    await membre.timeout(timedelta(seconds=duree), reason=f"mute {interaction.user}")
    embed = discord.Embed(
        description=f"🔇 {membre.mention} a été mute pour {duree} secondes.",
        color=discord.Color.greyple()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unmute", description="Retire le mute (timeout) d'un membre.")
@app_commands.describe(membre="Le membre à unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membre: discord.Member):
    await membre.timeout(None, reason=f"unmute {interaction.user}")
    embed = discord.Embed(
        description=f"🔊 {membre.mention} a été unmute.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


# ---------------------------------------------------------------------------
# Blacklist (anti-join)
# ---------------------------------------------------------------------------

@bot.tree.command(name="add_blacklist", description="Ajoute un membre à la blacklist anti-join.")
@app_commands.checks.has_permissions(administrator=True)
async def add_blacklist(interaction: discord.Interaction, membre: discord.Member):
    BLACKLIST_USERS.add(membre.id)
    await interaction.response.send_message(f"🚫 {membre.mention} a été **ajouté** à la blacklist (anti-join).")


@bot.tree.command(name="remove_blacklist", description="Retire un membre de la blacklist anti-join.")
@app_commands.checks.has_permissions(administrator=True)
async def remove_blacklist(interaction: discord.Interaction, membre: discord.Member):
    BLACKLIST_USERS.discard(membre.id)
    await interaction.response.send_message(f"✅ {membre.mention} a été **retiré** de la blacklist (anti-join).")


@bot.tree.command(name="show_blacklist", description="Affiche la blacklist anti-join.")
@app_commands.checks.has_permissions(administrator=True)
async def show_blacklist(interaction: discord.Interaction):
    if not BLACKLIST_USERS:
        return await interaction.response.send_message("✅ La blacklist (anti-join) est **vide**.")

    noms = [f"<@{uid}>" for uid in BLACKLIST_USERS]
    await interaction.response.send_message("🚫 **Blacklist (anti-join) :**\n" + "\n".join(noms))


# ---------------------------------------------------------------------------
# Fun
# ---------------------------------------------------------------------------

@bot.tree.command(name="insulte", description="Envoie une insulte fun à un membre.")
@fun_role_or_admin()
async def insulte(interaction: discord.Interaction, membre: discord.Member):
    embed = discord.Embed(
        description=f"{membre.mention}, {random.choice(ROASTS)}",
        color=discord.Color.magenta()
    )
    await interaction.response.send_message(embed=embed)


# !shame répondait à un message : en slash command ça devient une "commande
# contextuelle" -> clic droit sur un message > Apps > Shame.
@bot.tree.context_menu(name="Shame")
@app_commands.checks.cooldown(1, 10.0)
async def shame_context(interaction: discord.Interaction, message: discord.Message):
    try:
        auteur = message.author
        contenu = message.content.strip() if message.content else "[Message sans texte]"

        embed = discord.Embed(
            title="📢 SHAME",
            description=(
                f"💀 Regardez ce que {auteur.mention} :\n\n"
                f"```{contenu}```\n"
                f"🔥 Insultez-lui ses ancêtres."
            ),
            color=discord.Color.dark_red()
        )

        embed.add_field(
            name="Message original",
            value=f"[Aller au message]({message.jump_url})",
            inline=False
        )

        embed.set_footer(
            text=f"Shame lancé par {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(
            content="@here",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=True,
                users=True,
                roles=True,
                replied_user=False
            )
        )

    except Exception as e:
        print(f"[shame error] {e}")
        await interaction.response.send_message(f"❌ Erreur dans Shame : `{e}`", ephemeral=True)


@bot.tree.command(name="insulte_random", description="Roast un membre au hasard du serveur.")
@fun_role_or_admin()
async def insulte_random(interaction: discord.Interaction):
    humains = [m for m in interaction.guild.members if not m.bot and m != interaction.user]
    if not humains:
        return await interaction.response.send_message("Personne à insulter 😅")

    cible = random.choice(humains)
    embed = discord.Embed(
        description=f"{cible.mention}, {random.choice(ROASTS)}",
        color=discord.Color.magenta()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="cat", description="Envoie un chat sacré.")
@fun_role_or_admin()
async def cat(interaction: discord.Interaction):
    embed = discord.Embed(
        title="😺 Chat sacré",
        description="Un chat si expressif...",
        color=discord.Color.orange()
    )
    embed.set_image(url="https://media.tenor.com/Bg3ShfbkKJwAAAAC/rigby-cat-rigby.gif")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="skillissue", description="Skill Issue.")
@fun_role_or_admin()
async def skillissue(interaction: discord.Interaction):
    images = ["image4.png", "skill_issue.png"]
    chosen = random.choice(images)

    embed = discord.Embed(
        title="💢 Skill Issue",
        description="Un manque de compétence détecté...",
        color=discord.Color.red()
    )

    file = discord.File(chosen, filename=chosen)
    embed.set_image(url=f"attachment://{chosen}")

    await interaction.response.send_message(embed=embed, file=file)


@bot.tree.command(name="nuke", description="💣 Simulation de nuke (100% fake, juste pour le fun).")
@app_commands.checks.has_permissions(administrator=True)
async def nuke(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☢️ NUKE DU SERV",
        description="Ton serveur il est foutu…",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed)

    await asyncio.sleep(1)
    await interaction.edit_original_response(embed=discord.Embed(
        title="☢️ NUKE DU SERV",
        description="💣 Destruction du serveur dans **3**…",
        color=discord.Color.dark_red()
    ))

    await asyncio.sleep(1)
    await interaction.edit_original_response(embed=discord.Embed(
        title="☢️ NUKE DU SERV",
        description="💣 Destruction du serveur dans **2**…",
        color=discord.Color.dark_red()
    ))

    await asyncio.sleep(1)
    await interaction.edit_original_response(embed=discord.Embed(
        title="☢️ NUKE DU SERV",
        description="💣 Destruction du serveur dans **1**…",
        color=discord.Color.dark_red()
    ))

    await asyncio.sleep(2)
    await interaction.edit_original_response(embed=discord.Embed(
        title="❌ LE SERV EST MORT",
        description=(
            "💥 **SERVEUR DEAD**\n\n"
            "Naaaaaan je déconne ya rien mdrrrrr\n"
        ),
        color=discord.Color.green()
    ))


# !roulette prenait un nombre variable de mentions (*membres). Les slash
# commands ne supportent pas les arguments variadiques : on passe donc par
# 5 emplacements optionnels (ajuste ce nombre si besoin).
@bot.tree.command(name="roulette", description="Ban Gambling : mute aléatoirement un des joueurs pendant 10 minutes.")
@app_commands.describe(
    membre1="Joueur 1", membre2="Joueur 2", membre3="Joueur 3 (optionnel)",
    membre4="Joueur 4 (optionnel)", membre5="Joueur 5 (optionnel)"
)
@app_commands.checks.has_permissions(administrator=True)
async def roulette(
    interaction: discord.Interaction,
    membre1: discord.Member,
    membre2: discord.Member,
    membre3: Optional[discord.Member] = None,
    membre4: Optional[discord.Member] = None,
    membre5: Optional[discord.Member] = None,
):
    membres = [m for m in (membre1, membre2, membre3, membre4, membre5) if m is not None]
    participants = [m for m in membres if not m.bot]

    if len(participants) < 2:
        return await interaction.response.send_message("❌ Les bots ne jouent pas. Mentionne au moins **2 humains**.", ephemeral=True)

    perdant = random.choice(participants)

    try:
        await perdant.timeout(
            timedelta(minutes=10),
            reason=f"Perdant à la roulette russe (par {interaction.user})"
        )
    except discord.errors.HTTPException as e:
        if e.status != 204:
            print(f"[roulette timeout] {e}")
            return await interaction.response.send_message(
                f"⚠️ Impossible de mute {perdant.mention}. Vérifie mes permissions.", ephemeral=True
            )
    except Exception as e:
        print(f"[roulette timeout] {e}")
        return await interaction.response.send_message(f"⚠️ Erreur inattendue pendant le mute : {e}", ephemeral=True)

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
        text=f"Lancée par {interaction.user}",
        icon_url=getattr(interaction.user.avatar, "url", None)
    )

    await interaction.response.send_message(embed=embed)
    await interaction.followup.send(
        f"💥 {perdant.mention} a perdu la roulette russe ! "
        "Il est réduit au silence pendant 10 minutes 😈"
    )


@bot.tree.command(name="femboy", description="Envoie une image femboy.")
@fun_role_or_admin()
@app_commands.checks.cooldown(1, 5.0)
async def femboy(interaction: discord.Interaction):
    global LAST_FEMBOY_IMAGES, LAST_FEMBOY_CHARACTERS
    await interaction.response.defer()

    try:
        url = "https://safebooru.org/index.php"
        all_posts = []

        async with aiohttp.ClientSession() as session:
            for _ in range(3):
                tags = random.choice(FEMBOY_TAGS)

                async with session.get(
                    url,
                    params={
                        "page": "dapi",
                        "s": "post",
                        "q": "index",
                        "json": 1,
                        "tags": tags,
                        "limit": 100,
                        "pid": random.randint(0, 30)
                    },
                    headers={"User-Agent": "HirashiBot/1.0"}
                ) as response:

                    print(f"[femboy] tags={tags} status={response.status}", flush=True)

                    if response.status != 200:
                        text = await response.text()
                        print(f"[femboy] body={text[:300]}", flush=True)
                        continue

                    data = await response.json(content_type=None)

                    if isinstance(data, list):
                        all_posts.extend(data)

        if not all_posts:
            return await interaction.followup.send("❌ Aucun résultat trouvé.")

        seen_ids = set()
        unique_posts = []

        for post in all_posts:
            pid = post.get("id")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            unique_posts.append(post)

        posts_valides = []

        for post in unique_posts:
            image_url = post.get("file_url") or post.get("large_file_url")
            if not image_url:
                continue

            lower_url = image_url.lower()
            if not any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue

            if image_url in LAST_FEMBOY_IMAGES:
                continue

            tag_string = post.get("tags", "")
            character = extract_recent_femboy_character(tag_string)

            if character and character in LAST_FEMBOY_CHARACTERS:
                continue

            posts_valides.append(post)

        if not posts_valides:
            LAST_FEMBOY_IMAGES.clear()
            LAST_FEMBOY_CHARACTERS.clear()

            for post in unique_posts:
                image_url = post.get("file_url") or post.get("large_file_url")
                if not image_url:
                    continue

                lower_url = image_url.lower()
                if not any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    continue

                posts_valides.append(post)

        if not posts_valides:
            return await interaction.followup.send("❌ Aucune image valide trouvée.")

        post = random.choice(posts_valides)
        image_url = post.get("file_url") or post.get("large_file_url")

        tag_string = post.get("tags", "")
        character = extract_recent_femboy_character(tag_string)

        LAST_FEMBOY_IMAGES.append(image_url)
        if len(LAST_FEMBOY_IMAGES) > MAX_FEMBOY_HISTORY:
            LAST_FEMBOY_IMAGES.pop(0)

        if character:
            LAST_FEMBOY_CHARACTERS.append(character)
            if len(LAST_FEMBOY_CHARACTERS) > MAX_FEMBOY_CHARACTER_HISTORY:
                LAST_FEMBOY_CHARACTERS.pop(0)

        embed = discord.Embed(
            title="💖 Femboy",
            color=discord.Color.pink()
        )
        embed.set_image(url=image_url)

        post_id = post.get("id")
        if post_id:
            embed.add_field(
                name="Source",
                value=f"https://safebooru.org/index.php?page=post&s=view&id={post_id}",
                inline=False
            )

        if character:
            embed.set_footer(text=f"Personnage détecté : {character}")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"[femboy error] {type(e).__name__}: {e}", flush=True)
        await interaction.followup.send(f"❌ Erreur API : {type(e).__name__}")


@bot.tree.command(name="uma", description="Envoie une image Umamusume, avec ou sans personnage précis.")
@fun_role_or_admin()
@app_commands.describe(personnage="Ex : oguri, teio, mcqueen, goldship, rice, kita, satono")
@app_commands.checks.cooldown(1, 5.0)
async def uma(interaction: discord.Interaction, personnage: Optional[str] = None):
    await interaction.response.defer()

    try:
        if personnage:
            personnage = personnage.lower().strip()

        if personnage and personnage in UMA_CHARACTER_TAGS:
            tags = f"{UMA_CHARACTER_TAGS[personnage]} {UMA_BASE_TAGS}"
            titre = f"🏇 Uma Musume - {personnage.capitalize()}"
        else:
            tags = UMA_BASE_TAGS
            titre = "🏇 Uma Musume"

        url = "https://safebooru.org/index.php"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={
                    "page": "dapi",
                    "s": "post",
                    "q": "index",
                    "json": 1,
                    "tags": tags,
                    "limit": 100,
                    "pid": random.randint(0, 30)
                },
                headers={"User-Agent": "HirashiBot/1.0"}
            ) as response:

                print(f"[uma] tags = {tags}", flush=True)
                print(f"[uma] status = {response.status}", flush=True)

                if response.status != 200:
                    text = await response.text()
                    print(f"[uma] body = {text[:300]}", flush=True)
                    return await interaction.followup.send(f"❌ API indisponible ({response.status})")

                data = await response.json(content_type=None)

        if not data:
            if personnage and personnage not in UMA_CHARACTER_TAGS:
                return await interaction.followup.send("❌ Personnage inconnu. Exemples : `/uma oguri`, `/uma teio`")
            return await interaction.followup.send("❌ Aucun résultat trouvé.")

        posts_valides = []

        for post in data:
            image_url = post.get("file_url") or post.get("large_file_url")
            if not image_url:
                continue

            lower_url = image_url.lower()
            if not any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue

            post_tags = set(post.get("tags", "").split())

            if post_tags & UMA_BLACKLIST:
                continue

            if image_url in LAST_UMA_IMAGES:
                continue

            posts_valides.append(post)

        if not posts_valides:
            LAST_UMA_IMAGES.clear()

            for post in data:
                image_url = post.get("file_url") or post.get("large_file_url")
                if not image_url:
                    continue

                lower_url = image_url.lower()
                if not any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    continue

                post_tags = set(post.get("tags", "").split())

                if post_tags & UMA_BLACKLIST:
                    continue

                posts_valides.append(post)

        if not posts_valides:
            return await interaction.followup.send("❌ Aucune image valide trouvée.")

        post = random.choice(posts_valides)
        image_url = post.get("file_url") or post.get("large_file_url")

        LAST_UMA_IMAGES.append(image_url)
        if len(LAST_UMA_IMAGES) > MAX_UMA_HISTORY:
            LAST_UMA_IMAGES.pop(0)

        embed = discord.Embed(
            title=titre,
            color=discord.Color.purple()
        )
        embed.set_image(url=image_url)

        post_id = post.get("id")
        if post_id:
            embed.add_field(
                name="Source",
                value=f"https://safebooru.org/index.php?page=post&s=view&id={post_id}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"[uma error] {type(e).__name__}: {e}", flush=True)
        await interaction.followup.send(f"❌ Erreur API : {type(e).__name__}")


@bot.tree.command(name="cailloux", description="Envoie une image Houseki no Kuni.")
@fun_role_or_admin()
@app_commands.describe(personnage="Ex : phos, cinnabar, diamond, bort, rutile, antarcticite")
@app_commands.checks.cooldown(1, 5.0)
async def cailloux(interaction: discord.Interaction, personnage: Optional[str] = None):
    await interaction.response.defer()

    try:
        if personnage:
            personnage = personnage.lower().strip()

        if personnage and personnage in HOUSEKI_CHARACTER_TAGS:
            tags = f"{HOUSEKI_CHARACTER_TAGS[personnage]} {HOUSEKI_BASE_TAGS}"
            titre = f"💎 Houseki no Kuni - {personnage.capitalize()}"
        else:
            tags = HOUSEKI_BASE_TAGS
            titre = "💎 Houseki no Kuni"

        url = "https://safebooru.org/index.php"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={
                    "page": "dapi",
                    "s": "post",
                    "q": "index",
                    "json": 1,
                    "tags": tags,
                    "limit": 100,
                    "pid": random.randint(0, 30)
                },
                headers={"User-Agent": "HirashiBot/1.0"}
            ) as response:

                print(f"[cailloux] tags={tags} status={response.status}", flush=True)

                if response.status != 200:
                    return await interaction.followup.send(
                        f"❌ API indisponible ({response.status})"
                    )

                data = await response.json(content_type=None)

        if not data:
            if personnage and personnage not in HOUSEKI_CHARACTER_TAGS:
                return await interaction.followup.send(
                    "❌ Personnage inconnu. Exemples : `/cailloux phos`, `/cailloux cinnabar`, `/cailloux bort`"
                )
            return await interaction.followup.send("❌ Aucun résultat trouvé.")

        posts_valides = []

        for post in data:
            image_url = post.get("file_url") or post.get("large_file_url")
            if not image_url:
                continue

            lower_url = image_url.lower()
            if not any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue

            post_tags = set(post.get("tags", "").split())

            if post_tags & HOUSEKI_BLACKLIST:
                continue

            if image_url in LAST_HOUSEKI_IMAGES:
                continue

            posts_valides.append(post)

        if not posts_valides:
            LAST_HOUSEKI_IMAGES.clear()

            for post in data:
                image_url = post.get("file_url") or post.get("large_file_url")
                if not image_url:
                    continue

                lower_url = image_url.lower()
                if not any(ext in lower_url for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    continue

                post_tags = set(post.get("tags", "").split())
                if post_tags & HOUSEKI_BLACKLIST:
                    continue

                posts_valides.append(post)

        if not posts_valides:
            return await interaction.followup.send("❌ Aucune image valide trouvée.")

        post = random.choice(posts_valides)
        image_url = post.get("file_url") or post.get("large_file_url")

        LAST_HOUSEKI_IMAGES.append(image_url)
        if len(LAST_HOUSEKI_IMAGES) > MAX_HOUSEKI_HISTORY:
            LAST_HOUSEKI_IMAGES.pop(0)

        embed = discord.Embed(title=titre, color=discord.Color.teal())
        embed.set_image(url=image_url)

        post_id = post.get("id")
        if post_id:
            embed.add_field(
                name="Source",
                value=f"https://safebooru.org/index.php?page=post&s=view&id={post_id}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"[cailloux error] {type(e).__name__}: {e}", flush=True)
        await interaction.followup.send(f"❌ Erreur API : {type(e).__name__}")


# Renommé en minuscule : Discord impose que les noms de slash commands
# soient entièrement en minuscules ("Nahidwin" -> "nahidwin").
@bot.tree.command(name="nahidwin", description="Envoie une image Nah I'd win au hasard.")
@fun_role_or_admin()
async def nahidwin(interaction: discord.Interaction):
    folder = "images"
    try:
        fichiers = [
            f for f in os.listdir(folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        ]
    except FileNotFoundError:
        return await interaction.response.send_message("❌ Dossier `images` introuvable, vérifie qu'il est bien à la racine du projet.", ephemeral=True)

    if not fichiers:
        return await interaction.response.send_message("❌ Il n'y a aucune image dans le dossier `images`.", ephemeral=True)

    fichier_choisi = random.choice(fichiers)
    chemin_complet = os.path.join(folder, fichier_choisi)

    file = discord.File(chemin_complet, filename=fichier_choisi)

    embed = discord.Embed(
        title="Nah I'd win",
        description="Quel Gojo on a aujourd'hui ?",
        color=discord.Color.purple()
    )
    embed.set_image(url=f"attachment://{fichier_choisi}")

    await interaction.response.send_message(embed=embed, file=file)



@bot.tree.command(name="say", description="Fait dire un message au bot.")
@fun_role_or_admin()
@app_commands.describe(message="Le message que le bot doit envoyer")
@app_commands.checks.cooldown(1, 3.0)
async def say(interaction: discord.Interaction, message: str):
    if not message.strip():
        return await interaction.response.send_message(
            "❌ Le message ne peut pas être vide.",
            ephemeral=True
        )

    if len(message) > 2000:
        return await interaction.response.send_message(
            "❌ Le message dépasse la limite Discord de 2 000 caractères.",
            ephemeral=True
        )

    await interaction.response.send_message(
        "✅ Message envoyé.",
        ephemeral=True
    )

    await interaction.channel.send(
        message,
        allowed_mentions=discord.AllowedMentions.none()
    )


@bot.tree.command(
    name="dialogue",
    description="Crée une boîte de dialogue style Undertale/Deltarune."
)
@fun_role_or_admin()
@app_commands.describe(
    texte="Le texte à afficher",
    personnage="Facultatif : nom du PNG dans assets/portraits, ex. ralsei"
)
@app_commands.checks.cooldown(1, 5.0)
async def dialogue(
    interaction: discord.Interaction,
    texte: str,
    personnage: Optional[str] = None
):
    texte = texte.strip()
    personnage = personnage.strip() if personnage else None

    if not texte:
        return await interaction.response.send_message(
            "❌ Le texte ne peut pas être vide.",
            ephemeral=True
        )

    if len(texte) > 700:
        return await interaction.response.send_message(
            "❌ Le dialogue est limité à 700 caractères.",
            ephemeral=True
        )

    await interaction.response.defer()

    try:
        avatar_bytes = None

        # Aucun personnage choisi : on récupère l'avatar de l'utilisateur.
        if personnage is None:
            avatar_asset = interaction.user.display_avatar.with_size(256)
            avatar_bytes = await avatar_asset.read()

        image_buffer = create_dialogue_image(
            texte=texte,
            personnage=personnage,
            avatar_bytes=avatar_bytes
        )

        discord_file = discord.File(image_buffer, filename="dialogue.png")
        await interaction.followup.send(file=discord_file)

    except FileNotFoundError as error:
        await interaction.followup.send(
            f"❌ {error}",
            ephemeral=True
        )
    except Exception as error:
        print(f"[dialogue error] {type(error).__name__}: {error}", flush=True)
        await interaction.followup.send(
            f"❌ Impossible de créer le dialogue : `{type(error).__name__}`",
            ephemeral=True
        )


@bot.tree.command(name="help", description="Affiche la liste des commandes du bot.")
async def help_command(interaction: discord.Interaction):
    e = discord.Embed(title="🛡️ Commandes du bot", color=discord.Color.blue())
    e.add_field(name="🔨 /ban / 👢 /kick", value="Bannir / expulser un membre", inline=False)
    e.add_field(name="🔇 /mute / 🔊 /unmute", value="Timeout (mute) ou unmute un membre", inline=False)
    e.add_field(name="⚠️ /warn membre [raison]", value="Avertir un membre (à 3 warns, il est kick)", inline=False)
    e.add_field(name="♻️ /unwarn membre", value="Retire un avertissement au membre", inline=False)
    e.add_field(name="🧹 /clear nombre", value="Supprimer n messages", inline=False)
    e.add_field(name="🧹 /clear_user membre", value="Supprimer messages d'un membre", inline=False)
    e.add_field(name="🚫 Blacklist (anti-join)", value="/add_blacklist | /remove_blacklist | /show_blacklist", inline=False)
    e.add_field(name="🤬 /insulte membre", value="Envoie une insulte fun", inline=False)
    e.add_field(name="📢 Shame", value="Clic droit sur un message → Apps → Shame", inline=False)
    e.add_field(name="💖 /femboy", value="Envoie une image via l'API femboy", inline=False)
    e.add_field(name="🏇 /uma [personnage]", value="Envoie une image Umamusume. Ex : `/uma oguri`", inline=False)
    e.add_field(name="💎 /cailloux [personnage]", value="Envoie une image Houseki no Kuni. Ex : `/cailloux phos`", inline=False)
    e.add_field(name="🎯 /insulte_random", value="Roast un membre au hasard", inline=False)
    e.add_field(name="🐈 /cat / 💢 /skillissue", value="Fun/Images", inline=False)
    e.add_field(name="🔫 /roulette membre1 membre2 ...", value="Mute un membre au hasard parmi les participants", inline=False)
    e.add_field(name="📸 /nahidwin", value="Envoie une image Nah I'd win au hasard", inline=False)
    e.add_field(name="💬 /say message", value="Fait dire un message au bot", inline=False)
    e.add_field(name="⬛ /dialogue texte [personnage]", value="Crée une boîte de dialogue style Undertale/Deltarune", inline=False)
    await interaction.response.send_message(embed=e)


# ---------------------------------------------------------------------------
# Démarrage
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")

    try:
        if TEST_GUILD_ID:
            guild_obj = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=guild_obj)
            synced = await bot.tree.sync(guild=guild_obj)
            print(f"📜 {len(synced)} commandes synchronisées sur le serveur de test {TEST_GUILD_ID}")
        else:
            synced = await bot.tree.sync()
            print(f"📜 {len(synced)} commandes synchronisées globalement (peut prendre jusqu'à 1h à apparaître)")
    except Exception as e:
        print(f"[sync error] {e}")

    activity = discord.Game("Jerkmate | Ranked")
    await bot.change_presence(status=discord.Status.online, activity=activity)


while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[CRASH] {e}\nRedémarrage dans 5s...")
        time.sleep(5)
