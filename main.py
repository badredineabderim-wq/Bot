import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# منع السبام البسيط
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    bad_words = ["spam", "hack", "raid"]

    for word in bad_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention} لا تسوي سبام 🚫")
            return

    await bot.process_commands(message)


# أمر بان
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member}")


# أمر كيك
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member}")


# أمر لوك
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 تم قفل الشات")


# أمر فتح
@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 تم فتح الشات")


bot.run("MTQ1Nzc1NTc0MTg3OTI3MTY1NA.GplhIW.5e_8tNrZLpP3Gb9X5Gxs6sym7aj0a2fDcVLgI8")
