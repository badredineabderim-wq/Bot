import discord
from discord.ext import commands
import time
import datetime
from collections import defaultdict
import os
from discord import app_commands
import asyncio

# ===== INTENTS =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SYSTEMS =====
spam = defaultdict(list)
mentions = defaultdict(list)
joins = defaultdict(list)
warnings = defaultdict(int)

TOKEN = os.getenv("TOKEN")

log_channel_id = 1496559896273879140

async def punish(member, channel=None):
    level = warnings[member.id]
    
    channel = member.guild.get_channel(log_channel_id)

    try:
        if level == 1:
            if channel:
                await channel.send(f"⚠️ {member.mention} تحذير (1)")

        elif level == 2:
            await member.timeout(
                datetime.timedelta(minutes=10),
                reason="AutoMod Level 2"
            )

        elif level == 3:
            await member.timeout(
                datetime.timedelta(minutes=30),
                reason="AutoMod Level 3"
            )

        elif level == 4:
            await member.timeout(
                datetime.timedelta(hours=2),
                reason="AutoMod Level 4"
            )

        elif level == 5:
            await member.timeout(
                datetime.timedelta(hours=4),
                reason="AutoMod Level 5"
            )

        elif level == 6:
            await member.timeout(
                datetime.timedelta(hours=8),
                reason="AutoMod Level 6"
            )

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
        invites_cache[guild.id] = await guild.invites()

    if not hasattr(bot, "reset_task_started"):
        bot.loop.create_task(reset_warnings_task())
        bot.reset_task_started = True

async def reset_warnings_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        warnings.clear()
        print("🔄 Warnings reset")
        await asyncio.sleep(86400)

# =========================
# 🛡️ MESSAGE PROTECTION
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
            await punish(message.author, message.channel)
            await message.channel.send("🚫 Spam detected", delete_after=3)
        except:
            pass
        return

    # ===== LINKS =====
    if "http" in message.content.lower():
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author, message.channel)
        except:
            pass
        return

    # ===== CAPS =====
    if message.content.isupper() and len(message.content) > 5:
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author, message.channel)
        except:
            pass
        return

    await bot.process_commands(message)

# =========================
# 💀 ANTI NUKE (SAFE)
# =========================
@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1):
            user = entry.user

            if user and user != channel.guild.owner and not user.guild_permissions.administrator:
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

            if user and user != role.guild.owner and not user.guild_permissions.administrator:
                await user.ban(reason="Role Abuse")
    except:
        pass


# =========================
# ⚙️ SLASH COMMANDS
# =========================
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong: {round(bot.latency * 1000)}ms"
    )


@bot.tree.command(name="warn", description="Warn a user")
async def warn(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] += 1
    await interaction.response.send_message(f"⚠️ Warned {member.mention}")


@bot.tree.command(name="clearwarns", description="Clear warnings")
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] = 0
    await interaction.response.send_message(f"🧹 Cleared warnings for {member.mention}")


@bot.tree.command(name="stats", description="User warnings")
async def stats(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    await interaction.response.send_message(
        f"📊 {member.mention} warnings: {warnings[member.id]}")

@bot.tree.command(name="mute", description="Mute a member")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):

    # صلاحية المستخدم
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ماعندك صلاحية (Moderate Members)",
            ephemeral=True) 

    # صلاحية البوت
    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ماعندي صلاحية الميوت",
            ephemeral=True)

    # حماية الرتب
    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "❌ ما أقدر أكتم عضو رتبته أعلى أو مساوية لي",
            ephemeral=True)

    try:
        await member.timeout(
            datetime.timedelta(minutes=minutes),
            reason=f"Muted by {interaction.user}")

        await interaction.response.send_message(
            f"🔇 تم كتم {member.mention} لمدة {minutes} دقيقة")

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ ما عندي صلاحية (Forbidden)",
            ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            f"❌ خطأ: {e}",
            ephemeral=True)
        
@bot.tree.command(name="unmute", description="Unmute a member")
async def unmute(interaction: discord.Interaction, member: discord.Member):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ ماعندك صلاحية", ephemeral=True)

    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ ماعندي صلاحية", ephemeral=True)

    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ ما أقدر أتعامل مع رتب أعلى", ephemeral=True)

    try:
        await member.edit(timed_out_until=None)
        await interaction.response.send_message(f"🔊 تم فك الميوت عن {member.mention}")

    except discord.Forbidden:
        await interaction.response.send_message("❌ ما عندي صلاحية (Forbidden)", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)
    
@bot.event
async def on_member_join(member):
    guild = member.guild
    now = time.time()

    # ===== RAID =====
    joins[guild.id].append(now)
    joins[guild.id] = [t for t in joins[guild.id] if now - t < RAID_WINDOW]

    account_age = (discord.utils.utcnow() - member.created_at).days

    if len(joins[guild.id]) >= RAID_LIMIT and account_age < 2:
        if guild.system_channel:
            await guild.system_channel.send("🚨 RAID DETECTED")

    # ===== INVITE =====
    try:
        new_invites = await guild.invites()
        old_invites = invites_cache.get(guild.id, [])

        inviter = None

        for new in new_invites:
            for old in old_invites:
                if new.code == old.code and new.uses > old.uses:
                    inviter = new.inviter
                    break

        invites_cache[guild.id] = new_invites

        if guild.system_channel:
            if inviter:
                await guild.system_channel.send(
                    f"📥 {member.name} دخل عن طريق {inviter.name}")
            else:
                await guild.system_channel.send(
                    f"📥 {member.name} دخل بدون دعوة")
    except:
        pass

# =========================
# RUN
# =========================
bot.run(TOKEN)
