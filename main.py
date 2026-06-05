import discord
from discord.ext import commands
import time
import datetime
from collections import defaultdict
import os
import asyncio

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
    channel = bot.get_channel(1496559896273879140)

    try:
        punishment = "لا يوجد"

        if level == 1:
            punishment = "⚠️ تحذير فقط"

        elif level == 2:
            await member.timeout(
                datetime.timedelta(minutes=10),
                reason="AutoMod Level 2"
            )
            punishment = "🔇 ميوت 10 دقائق"

        elif level == 3:
            await member.timeout(
                datetime.timedelta(minutes=30),
                reason="AutoMod Level 3"
            )
            punishment = "🔇 ميوت 30 دقيقة"

        elif level == 4:
            await member.timeout(
                datetime.timedelta(hours=2),
                reason="AutoMod Level 4"
            )
            punishment = "🔇 ميوت ساعتين"

        elif level == 5:
            await member.timeout(
                datetime.timedelta(hours=4),
                reason="AutoMod Level 5"
            )
            punishment = "🔇 ميوت 4 ساعات"

        elif level == 6:
            await member.timeout(
                datetime.timedelta(hours=8),
                reason="AutoMod Level 6"
            )
            punishment = "🔇 ميوت 8 ساعات"

        elif level == 7:
            await member.kick(reason="AutoMod Level 7")
            punishment = "👢 طرد"

        elif level >= 8:
            await member.ban(reason="AutoMod Level 8")
            punishment = "🔨 باند"

        if channel:
            await channel.send(
                f"⚠️ العضو: {member.mention}\n"
                f"📊 عدد التحذيرات: {level}\n"
                f"📌 العقوبة: {punishment}"
            )

    except discord.Forbidden:
        if channel:
            await channel.send(
                f"❌ ما أقدر أعاقب {member.mention} بسبب الصلاحيات"
            )

    except Exception as e:
        print(e)

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

    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < 3]

    if len(spam[uid]) >= 2:
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author)
            await message.channel.send("🚫 Spam detected", delete_after=3)
        except:
            pass
        return
        
        # ===== MENTION SPAM =====
if len(message.mentions) >= 4:

    if message.author.guild_permissions.administrator:
        return

    try:
        await message.delete()
        warnings[message.author.id] += 1
        await punish(message.author)

        await message.channel.send(
            f"🚫 {message.author.mention} لا يسمح بالمنشن الجماعي",
            delete_after=3)

    except Exception as e:
        print(e)

    return
    

# ===== DISCORD INVITES =====
    if (
        "discord.gg/" in message.content.lower()
        or "discord.com/invite/" in message.content.lower()):

        if message.author.guild_permissions.administrator:
            return

        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author)

            await message.channel.send(
                f"🚫 {message.author.mention} ممنوع نشر دعوات الديسكورد",
                delete_after=5)

        except Exception as e:
            print(e)

        return

    if message.content.isupper() and len(message.content) > 5:
        try:
            await message.delete()
            warnings[uid] += 1
            await punish(message.author)
        except:
            pass
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

    await interaction.response.send_message(
        f"⚠️ تم إعطاء ورن لـ {member.mention}\n"
        f"📊 المجموع: {warnings[member.id]}")
    
    warnings[member.id] += 1
    
    await interaction.response.send_message(f"⚠️ Warned {member.mention}")

@bot.tree.command(name="clearwarns")
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("No permission", ephemeral=True)

    warnings[member.id] = 0
    await interaction.response.send_message(f"🧹 Cleared warnings")

@bot.tree.command(name="stats")
async def stats(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    await interaction.response.send_message(f"📊 {warnings[member.id]}")

# =========================
# MUTE / UNMUTE (FIXED)
# =========================
@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ No permission", ephemeral=True)

    if not interaction.guild.me.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ Bot no permission", ephemeral=True)

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
        return await interaction.response.send_message("❌ Bot no permission", ephemeral=True)

    if member.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ Role too high", ephemeral=True)

    try:
        await member.edit(timed_out_until=None)
        await interaction.response.send_message(f"🔊 Unmuted {member.mention}")

    except Exception as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)

# =========================
# RAID + INVITES (FIXED)
# =========================
@bot.event
async def on_member_join(member):
    guild = member.guild
    now = time.time()

    joins[guild.id].append(now)
    joins[guild.id] = [t for t in joins[guild.id] if now - t < 8]

    if len(joins[guild.id]) >= 5:
        if guild.system_channel:
            await guild.system_channel.send("🚨 RAID DETECTED")

    try:
        new_invites = await guild.invites()
        old_invites = invites_cache.get(guild.id, {})

        inviter = None

        for invite in new_invites:
            old_uses = old_invites.get(invite.code, 0)

            if invite.uses > old_uses:
                inviter = invite.inviter
                break

        invites_cache[guild.id] = {
            i.code: i.uses for i in new_invites
        }

        if guild.system_channel:
            if inviter:
                await guild.system_channel.send(f"📥 {member.name} دخل عن طريق {inviter.name}")
            else:
                await guild.system_channel.send(f"📥 {member.name} دخل بدون دعوة")

    except Exception as e:
        print(e)

# =========================
# RUN
# =========================
bot.run(TOKEN)
