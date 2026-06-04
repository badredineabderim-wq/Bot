import discord
from discord.ext import commands
import time
import datetime
from collections import defaultdict
import os
from discord import app_commands

# ===== INTENTS =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SYSTEMS =====
spam = defaultdict(list)
mentions = defaultdict(list)
joins = defaultdict(list)
warnings = defaultdict(int)

TOKEN = os.getenv("TOKEN")

# ===== SETTINGS =====
SPAM_LIMIT = 3
SPAM_WINDOW = 3

MENTION_LIMIT = 4
MENTION_WINDOW = 5

RAID_LIMIT = 5
RAID_WINDOW = 8


# =========================
# READY
# =========================
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

    # ===== SPAM =====
    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < SPAM_WINDOW]

    if len(spam[uid]) >= SPAM_LIMIT:
        try:
            await message.delete()
            warnings[uid] += 1
            await message.channel.send("🚫 Spam detected", delete_after=3)
        except:
            pass
        return

    # ===== LINKS =====
    if "http" in message.content.lower():
        try:
            await message.delete()
            warnings[uid] += 1
        except:
            pass
        return

    # ===== CAPS =====
    if message.content.isupper() and len(message.content) > 5:
        try:
            await message.delete()
            warnings[uid] += 1
        except:
            pass
        return

    # ===== MENTION SPAM (IMPROVED) =====
    if len(message.mentions) >= 3 or len(message.role_mentions) >= 2:
        mentions[uid].append(now)
        mentions[uid] = [t for t in mentions[uid] if now - t < MENTION_WINDOW]

        if len(mentions[uid]) >= MENTION_LIMIT:
            try:
                await message.delete()
                warnings[uid] += 1
                await message.channel.send("🚫 Mention spam blocked", delete_after=3)
            except:
                pass
            return

    # ===== WARN SYSTEM (FIXED) =====
    if warnings[uid] >= 2:
        try:
            member = message.author
            await member.timeout(
                datetime.timedelta(minutes=15),
                reason="Auto Moderation"
            )
            warnings[uid] = 0
        except:
            pass

    await bot.process_commands(message)


# =========================
# 🚨 RAID PROTECTION (IMPROVED)
# =========================
@bot.event
async def on_member_join(member):
    gid = member.guild.id
    now = time.time()

    joins[gid].append(now)
    joins[gid] = [t for t in joins[gid] if now - t < RAID_WINDOW]

    account_age = (discord.utils.utcnow() - member.created_at).days

    # صارم لكن آمن
    if len(joins[gid]) >= RAID_LIMIT and account_age < 2:
        try:
            channel = member.guild.system_channel
            if channel:
                await channel.send("🚨 RAID DETECTED - Protection ON")
        except:
            pass


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
        f"📊 {member.mention} warnings: {warnings[member.id]}"
    )

@bot.tree.command(name="mute", description="Mute a member")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):

    # صلاحية المستخدم
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ماعندك صلاحية (Moderate Members)",
            ephemeral=True
        )

    # صلاحية البوت
    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ماعندي صلاحية الميوت",
            ephemeral=True
        )

    # حماية الرتب
    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "❌ ما أقدر أكتم عضو رتبته أعلى أو مساوية لي",
            ephemeral=True
        )

    try:
        await member.timeout(
            datetime.timedelta(minutes=minutes),
            reason=f"Muted by {interaction.user}"
        )

        await interaction.response.send_message(
            f"🔇 تم كتم {member.mention} لمدة {minutes} دقيقة"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ ما عندي صلاحية (Forbidden)",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ خطأ: {e}",
            ephemeral=True
        )
        @bot.tree.command(name="unmute", description="Unmute a member")
async def unmute(interaction: discord.Interaction, member: discord.Member):

    # صلاحيات المستخدم
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ماعندك صلاحية (Moderate Members)",
            ephemeral=True
        )

    # صلاحيات البوت
    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            "❌ ماعندي صلاحية إزالة الميوت",
            ephemeral=True
        )

    # حماية الرتب
    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message(
            "❌ ما أقدر أتعامل مع عضو رتبته أعلى أو مساوية لي",
            ephemeral=True
        )

    try:
        # الطريقة الصحيحة لفك الميوت
        await member.edit(timed_out_until=None)

        await interaction.response.send_message(
            f"🔊 تم فك الميوت عن {member.mention}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ ما عندي صلاحية (Forbidden)",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ خطأ: {e}",
            ephemeral=True
        )
# =========================
# RUN
# =========================
bot.run(TOKEN)
