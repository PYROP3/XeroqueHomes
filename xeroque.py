import asyncio
import discord
from discord.member import Member
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

legacy_commands = {}
taken_commands = ['dog', 'cat', 'search', 'help']

@bot.event
async def on_message(msg: discord.Message):
    if msg.author.id != bot.user.id:
        app.logger.debug(f"[{msg.channel.guild.name} / {msg.channel}] {msg.author} says \"{msg.content}\"")
        content = msg.content
        if content.startswith("--"):
            parsed = content[2:].split(' ')
            if len(parsed) > 0:
                if parsed[0] in legacy_commands:
                    pass
                else:
                    if parsed[0] not in taken_commands:
                        msg.reply("Psst {ctx.author}! Se você quer usar o comando de busca do Dog-Cat-Bot, tem que usar o comando `--search [conteúdo]`.\nNa dúvida, pode usar o `--help` para obter mais informações!")


async def _find_multi(ctx: SlashContext, users):
    app.logger.info(f"[{ctx.guild.name} / {ctx.channel}] Inbound request from {ctx.author} for user(s): [" + ", ".join([member.name for member in users]) + "]")
    msg = f"🔎 Hey {ctx.author}! Aqui está o resultado da minha investigação:"
    vcs = {}
    for member in users:
        found_this = False
        for vc in ctx.guild.voice_channels:
            if not found_this:
                app.logger.debug(f"[{ctx.guild.name} / {ctx.channel} / {ctx.author}] Members in {vc.name} -> [" + ", ".join([member.name for member in vc.members]) + "]")
                if member in vc.members:
                    app.logger.debug(f"[{ctx.guild.name} / {ctx.channel} / {ctx.author}] Found mentioned user {member} in vc {vc.name}")
                    found_this = True
                    try:
                        vcs[vc] += [prevent_selfmention(ctx, member)]
                    except KeyError:
                        vcs[vc] = [prevent_selfmention(ctx, member)]
        if not found_this:
            app.logger.debug(f"[{ctx.guild.name} / {ctx.channel} / {ctx.author}] Could not find {member}")
            try:
                vcs[None] += [prevent_selfmention(ctx, member)]
            except KeyError:
                vcs[None] = [prevent_selfmention(ctx, member)]
    for vc in vcs:
        if vc is not None:
            msg += "\n\t- " + userListToStr(vcs[vc]) + " " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em [{ctx.guild.get_channel(vc.category_id)}]{vc.mention}"
    if None in vcs:
        msg += "\n\t- " + userListToStr(vcs[None]) + " não " + ("está" if len(vcs[None]) == 1 else "estão") + f" em nenhum chat de voz"
    await ctx.send(content=msg, hidden=True)

async def _find_one(ctx, user):
    await _find_multi(ctx, [user])

def toOrdinal(n: int):
    return f"{n}th" if (n > 10 and n < 20) else "{}{}".format(n, ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"][n % 10])

def userListToStr(users) -> str:
    return ", ".join(users[:-1]) + f" e {users[-1]}" if len(users) > 1 else users[0]

def prevent_selfmention(ctx: SlashContext, member: Member):
    return member.mention if member.id != ctx.author.id else "você"

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
    msg = f"🔎 Hey {ctx.author}! Aqui está o resultado da minha investigação:"
    vcs = {}
    found_members = []
    for vc in ctx.guild.voice_channels:
        app.logger.debug(f"[{ctx.guild.name} / {ctx.channel} / {ctx.author}] Members in {vc.name} -> [" + ", ".join([member.name for member in vc.members]) + "]")
        for member in vc.members:
            if role in member.roles:
                app.logger.debug(f"[{ctx.guild.name} / {ctx.channel} / {ctx.author}] Found user {member} in vc {vc.name}")
                found_members += [member]
                try:
                    vcs[vc] += [prevent_selfmention(ctx, member)]
                except KeyError:
                    vcs[vc] = [prevent_selfmention(ctx, member)]
    for member in ctx.guild.members:
        if member not in found_members and role in member.roles:
            app.logger.debug(f"[{ctx.guild.name} / {ctx.channel} / {ctx.author}] Found user {member} not in vc")
            found_members += [member]
            try:
                vcs[None] += [prevent_selfmention(ctx, member)]
            except KeyError:
                vcs[None] = [prevent_selfmention(ctx, member)]

    for vc in vcs:
        if vc is not None:
            msg += "\n\t- " + userListToStr(vcs[vc]) + " " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em [{ctx.guild.get_channel(vc.category_id)}]{vc.mention}"
    if None in vcs:
        msg += "\n\t- " + userListToStr(vcs[None]) + " não " + ("está" if len(vcs[None]) == 1 else "estão") + f" em nenhum chat de voz"
    await ctx.send(content=msg, hidden=True)

@slash.context_menu(target=2, name="Find", guild_ids=guild_ids)
async def _find_contextual(ctx: SlashContext, *args, **kwargs):
    await _find_one(ctx, ctx.target_author)

bot.run(TOKEN)
