import discord
from discord.ext import commands
import time
from collections import defaultdict
import os

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SYSTEMS =====
spam = defaultdict(list)
joins = defaultdict(list)

# ===== SETTINGS =====
SPAM_LIMIT = 5
SPAM_WINDOW = 5

RAID_LIMIT = 5
RAID_WINDOW = 10


# ===== READY =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


# ===== ANTI-SPAM + ANTI-LINK =====
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = time.time()
    uid = message.author.id

    # ===== SPAM SYSTEM =====
    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < SPAM_WINDOW]

    if len(spam[uid]) > SPAM_LIMIT:
        try:
            await message.delete()
            await message.channel.send(
                f"🚫 {message.author.mention} لا تسوي سبام",
                delete_after=3
            )
        except:
            pass
        return

    # ===== LINK BLOCK =====
    if "http" in message.content.lower():
        if not message.author.guild_permissions.administrator:
            try:
                await message.delete()
                await message.channel.send(
                    "🚫 الروابط ممنوعة",
                    delete_after=3
                )
            except:
                pass
            return

    await bot.process_commands(message)


# ===== ANTI-RAID =====
@bot.event
async def on_member_join(member):
    now = time.time()
    gid = member.guild.id

    joins[gid].append(now)
    joins[gid] = [t for t in joins[gid] if now - t < RAID_WINDOW]

    if len(joins[gid]) >= RAID_LIMIT:
        channel = member.guild.system_channel
        if channel:
            await channel.send("🚨 Anti-Raid Activated!")

        # optional: lock server channels (basic protection)
        for channel in member.guild.text_channels:
            try:
                await channel.set_permissions(member.guild.default_role, send_messages=False)
            except:
                pass


# ===== SLASH COMMANDS =====
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong 🏓 {round(bot.latency * 1000)}ms")


@bot.tree.command(name="help", description="Bot commands")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🛡️ حماية البوت:\n"
        "/ping - سرعة البوت\n"
        "/help - الأوامر"
    )


# ===== RUN BOT =====
bot.run(os.getenv("TOKEN"))
