import asyncio
import discord
import discord_slash
import logging
import os
import sys
from discord import flags
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    print("DISCORD_TOKEN env var not set! Exiting")
    exit(1)

_ids = os.getenv('GUILD_IDS') or ""
_guild_ids = [int(id) for id in _ids.split('.') if id != ""]
guild_ids = _guild_ids if len(_guild_ids) else None

bot = commands.Bot(command_prefix="/", self_bot=True, intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)
app = Flask(__name__)
app.logger.root.setLevel(logging.getLevelName(os.getenv('LOG_LEVEL') or 'DEBUG'))
app.logger.addHandler(logging.StreamHandler(sys.stdout))

@bot.event
async def on_ready():
    app.logger.info(f"{bot.user} has connected to Discord")

@bot.event
async def on_message(msg: discord.Message):
    if msg.author.id != bot.user.id:
        app.logger.info(f"[{msg.channel.guild.name} / {msg.channel.name}] {msg.author.name} says \"{msg.content}\"")

async def _find_multi(ctx: SlashContext, users):
    app.logger.info(f"[{ctx.guild.name} / {ctx.channel.name}] Inbound request from {ctx.author.name} for user(s): [" + ", ".join([member.name for member in users]) + "]")
    msg = f"🔎 Hey {ctx.author.name}! Aqui está o resultado da minha investigação:"
    vcs = {}
    for member in users:
        found_this = False
        for vc in ctx.guild.voice_channels:
            if not found_this:
                app.logger.debug(f"[{ctx.guild.name} / {ctx.channel.name} / {ctx.author.name}] Members in {vc.name} -> [" + ", ".join([member.name for member in vc.members]) + "]")
                if member in vc.members:
                    app.logger.info(f"[{ctx.guild.name} / {ctx.channel.name} / {ctx.author.name}] Found mentioned user {member.name} in vc {vc.name}")
                    found_this = True
                    try:
                        vcs[vc] += [member]
                    except KeyError:
                        vcs[vc] = [member]
        if not found_this:
            app.logger.debug(f"[{ctx.guild.name} / {ctx.channel.name} / {ctx.author.name}] Could not find {member.name}")
            try:
                vcs[None] += [member]
            except KeyError:
                vcs[None] = [member]
    for vc in vcs:
        if vc is not None:
            msg += "\n\t- " + ", ".join([member.name for member in vcs[vc]]) + " " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em {vc.mention}"
    if None in vcs:
        msg += "\n\t- " + ", ".join([member.name for member in vcs[None]]) + " não " + ("está" if len(vcs[None]) == 1 else "estão") + f" em nenhum chat de voz"
    await ctx.send(content=msg, hidden=True)

async def _find_one(ctx, user):
    await _find_multi(ctx, [user])

def toOrdinal(n: int):
    return f"{n}th" if (n > 10 and n < 20) else "{}{}".format(n, ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"][n % 10])

n_users = 25

# Commands

opts = [discord_slash.manage_commands.create_option(name="user", description="1st user to find", option_type=6, required=True)]
for i in range(n_users - 1):
    opts += [discord_slash.manage_commands.create_option(name=f"additional_user{i}", description="{} user to find".format(toOrdinal(i + 2)), option_type=6, required=False)]
@slash.slash(name="find", description="Find users in voice channels", options=opts, guild_ids=guild_ids)
async def _find(ctx: SlashContext, **kwargs):
    users = [kwargs[user] for user in kwargs if kwargs[user] is not None]
    await _find_multi(ctx, users)

opts = [discord_slash.manage_commands.create_option(name="role", description="Squad to find", option_type=8, required=True)]
@slash.slash(name="findsquad", description="Find all users in a squad in voice channels", options=opts, guild_ids=guild_ids)
async def _find_squad(ctx: SlashContext, *args, **kwargs):
    role = kwargs['role']
    msg = f"🔎 Hey {ctx.author.name}! Aqui está o resultado da minha investigação:"
    vcs = {}
    found_members = []
    for vc in ctx.guild.voice_channels:
        app.logger.debug(f"[{ctx.guild.name} / {ctx.channel.name} / {ctx.author.name}] Members in {vc.name} -> [" + ", ".join([member.name for member in vc.members]) + "]")
        for member in vc.members:
            if role in member.roles:
                app.logger.debug(f"[{ctx.guild.name} / {ctx.channel.name} / {ctx.author.name}] Found user {member.name} in vc {vc.name}")
                found_members += [member]
                try:
                    vcs[vc] += [member]
                except KeyError:
                    vcs[vc] = [member]
    for member in ctx.guild.members:
        if member not in found_members and role in member.roles:
            app.logger.debug(f"[{ctx.guild.name} / {ctx.channel.name} / {ctx.author.name}] Found user {member.name} not in vc")
            found_members += [member]
            try:
                vcs[None] += [member]
            except KeyError:
                vcs[None] = [member]

    for vc in vcs:
        if vc is not None:
            msg += "\n\t- " + ", ".join([member.name for member in vcs[vc]]) + " " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em {vc.mention}"
    if None in vcs:
        msg += "\n\t- " + ", ".join([member.name for member in vcs[None]]) + " não " + ("está" if len(vcs[None]) == 1 else "estão") + f" em nenhum chat de voz"
    await ctx.send(content=msg, hidden=True)

@slash.context_menu(target=2, name="Find", guild_ids=guild_ids)
async def _find_contextual(ctx: SlashContext, *args, **kwargs):
    await _find_one(ctx, ctx.target_author)

bot.run(TOKEN)
