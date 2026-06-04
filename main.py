import discord
from discord.ext import commands
import time
import datetime
from collections import defaultdict
import os

# ===== INTENTS =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SYSTEMS =====
spam = defaultdict(list)
joins = defaultdict(list)
warnings = defaultdict(int)

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")

SPAM_LIMIT = 5
SPAM_WINDOW = 5

RAID_LIMIT = 5
RAID_WINDOW = 10


# ===== READY =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


# =========================
# 🛡️ MESSAGE PROTECTION
# =========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = time.time()

    # ===== SPAM SYSTEM =====
    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < SPAM_WINDOW]

    if len(spam[uid]) > SPAM_LIMIT:
        try:
            await message.delete()
            warnings[uid] += 1
            await message.channel.send("🚫 Spam detected", delete_after=3)
        except:
            pass
        return

    # ===== LINK BLOCK =====
    if "http" in message.content.lower():
        try:
            await message.delete()
            warnings[uid] += 1
            await message.channel.send("🚫 Links not allowed", delete_after=3)
        except:
            pass
        return

    # ===== WARN CHECK =====
    if warnings[uid] >= 3:
        try:
            await message.author.timeout(
                discord.utils.utcnow() + datetime.timedelta(minutes=10),
                reason="Auto Moderation"
            )
            warnings[uid] = 0
        except:
            pass

    await bot.process_commands(message)


# =========================
# 🚨 RAID PROTECTION (FIXED)
# =========================
@bot.event
async def on_member_join(member):
    gid = member.guild.id
    now = time.time()

    joins[gid].append(now)
    joins[gid] = [t for t in joins[gid] if now - t < RAID_WINDOW]

    account_age = (discord.utils.utcnow() - member.created_at).days

    # FIXED: more stable logic
    if len(joins[gid]) >= RAID_LIMIT and account_age < 3:
        try:
            channel = member.guild.system_channel
            if channel:
                await channel.send("🚨 RAID DETECTED - Protection Activated")
        except:
            pass


# =========================
# 💀 ANTI NUKE (SAFE VERSION)
# =========================
@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1):
            user = entry.user

            if user:
                # prevent owner/admin issues
                if user and user.id != channel.guild.owner_id and not user.guild_permissions.administrator:
                    await user.ban(reason="Anti-Nuke Protection")
    except:
        pass


# =========================
# 🧱 ROLE DELETE PROTECTION
# =========================
@bot.event
async def on_guild_role_delete(role):
    try:
        async for entry in role.guild.audit_logs(limit=1):
            user = entry.user

            if user:
                if user != role.guild.owner and not user.guild_permissions.administrator:
                    await user.ban(reason="Role Deletion Abuse")
    except:
        pass


# =========================
# 📦 CHANNEL CREATE ABUSE
# =========================
@bot.event
async def on_guild_channel_create(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1):
            user = entry.user

            if user:
                if user != channel.guild.owner and not user.guild_permissions.administrator:
                    await user.ban(reason="Channel Spam Abuse")
    except:
        pass


# =========================
# ⚙️ SLASH COMMANDS
# =========================
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 {round(bot.latency * 1000)}ms"
    )


@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] += 1
    await interaction.response.send_message(f"Warned {member}")


@bot.tree.command(name="clearwarns")
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] = 0
    await interaction.response.send_message("Warnings cleared")


# =========================
# RUN BOT
# =========================
bot.run(TOKEN)
