import discord
from discord.ext import commands
import time
import datetime
from collections import defaultdict
import os
import asyncio
from discord.ext import tasks

# ===== INTENTS =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SYSTEMS =====
spam = defaultdict(list)
mentions = defaultdict(list)
joins = defaultdict(list)
warnings = defaultdict(int)
invites_cache = {}

TOKEN = os.getenv("TOKEN")
log_channel_id = 1496559896273879140

# =========================
# PUNISH SYSTEM
# =========================
async def punish(member):
    level = warnings[member.id]
    channel = bot.get_channel(log_channel_id)

    try:
        if level == 1:
            if channel:
                await channel.send(f"⚠️ {member.mention} تحذير (1)")

        elif level == 2:
            await member.timeout(datetime.timedelta(minutes=10), reason="AutoMod Level 2")

        elif level == 3:
            await member.timeout(datetime.timedelta(minutes=30), reason="AutoMod Level 3")

        elif level == 4:
            await member.timeout(datetime.timedelta(hours=2), reason="AutoMod Level 4")

        elif level == 5:
            await member.timeout(datetime.timedelta(hours=4), reason="AutoMod Level 5")

        elif level == 6:
            await member.timeout(datetime.timedelta(hours=8), reason="AutoMod Level 6")

        elif level == 7:
            await member.kick(reason="AutoMod Level 7")

        elif level >= 8:
            await member.ban(reason="AutoMod Level 8")

    except Exception as e:
        print(e)

# ===== SETTINGS =====
SPAM_LIMIT = 3
SPAM_WINDOW = 3

MENTION_LIMIT = 4
MENTION_WINDOW = 5

RAID_LIMIT = 5
RAID_WINDOW = 8

invites_cache = {}

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

    for guild in bot.guilds:
        try:
            invites_cache[guild.id] = await guild.invites()
        except:
            invites_cache[guild.id] = {}

# =========================
# MESSAGE PROTECTION
# =========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = time.time()

    # ===== SPAM =====
    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < SPAM_WINDOW]

    if len(spam[uid]) >= SPAM_LIMIT:
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author)
            await message.channel.send("🚫 Spam detected", delete_after=3)

        except Exception as e:
            print(e)

        return

    # ===== LINKS =====
    if "http" in message.content.lower():
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author)

        except Exception as e:
            print(e)

        return

    # ===== CAPS =====
    if message.content.isupper() and len(message.content) > 5:
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author)

        except Exception as e:
            print(e)

        return

    await bot.process_commands(message)

# =========================
# ANTI NUKE
# =========================
@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1):
            user = entry.user

            if user and user != channel.guild.owner and not user.guild_permissions.administrator:
                await user.ban(reason="Anti-Nuke")

    except Exception as e:
        print(e)


@bot.event
async def on_guild_role_delete(role):
    try:
        async for entry in role.guild.audit_logs(limit=1):
            user = entry.user

            if user and user != role.guild.owner and not user.guild_permissions.administrator:
                await user.ban(reason="Role Abuse")

    except Exception as e:
        print(e)

# =========================
# SLASH COMMANDS
# =========================
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")


@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] += 1
    await interaction.response.send_message(f"⚠️ Warned {member.mention}")


@bot.tree.command(name="clearwarns")
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] = 0
    await interaction.response.send_message(f"🧹 Cleared warnings for {member.mention}")


@bot.tree.command(name="stats")
async def stats(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    await interaction.response.send_message(f"📊 {member.mention} warnings: {warnings[member.id]}")


# =========================
# MUTE / UNMUTE
# =========================
@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ No permission", ephemeral=True)

    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ Bot has no permission", ephemeral=True)

    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ Role too high", ephemeral=True)

    try:
        await member.timeout(datetime.timedelta(minutes=minutes))
        await interaction.response.send_message(f"🔇 Muted {member.mention}")

    except Exception as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)


@bot.tree.command(name="unmute")
async def unmute(interaction: discord.Interaction, member: discord.Member):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ No permission", ephemeral=True)

    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ Bot has no permission", ephemeral=True)

    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ Role too high", ephemeral=True)
        
# =========================
# RAID + INVITES
# =========================
@bot.event
async def on_member_join(member):
    guild = member.guild
    now = time.time()

    joins[guild.id].append(now)
    joins[guild.id] = [t for t in joins[guild.id] if now - t < RAID_WINDOW]

    if len(joins[guild.id]) >= RAID_LIMIT:
        if guild.system_channel:
            await guild.system_channel.send("🚨 RAID DETECTED")

    try:
    invites_before = invites_cache.get(guild.id, {})
    invites_after = await guild.invites()

    inviter = None

    for invite in invites_after:
        before = invites_before.get(invite.code)

        if before and invite.uses > before:
            inviter = invite.inviter
            break

    invites_cache[guild.id] = {
        invite.code: invite.uses for invite in invites_after
    }

    if guild.system_channel:
        if inviter:
            await guild.system_channel.send(
                f"📥 {member.name} دخل عن طريق {inviter.name}"
            )
        else:
            await guild.system_channel.send(
                f"📥 {member.name} دخل بدون دعوة"
            )

except Exception as e:
    print(e)
# =========================
# RUN
# =========================
bot.run(TOKEN)
