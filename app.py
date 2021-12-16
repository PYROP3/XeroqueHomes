import asyncio
import discord
import discord_slash
import os
import logging
from discord import flags
from flask import Flask
from dotenv import load_dotenv
from threading import Thread
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

_ids = os.getenv('GUILD_IDS') or ""
_guild_ids = [int(id) for id in _ids.split('.')]
guild_ids = _guild_ids if len(_guild_ids) else None

bot = commands.Bot(command_prefix="/", self_bot=True, intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)
app = Flask(__name__)
app.logger.root.setLevel(logging.getLevelName(os.getenv('LOG_LEVEL') or 'DEBUG'))

@app.route("/")
def hello_world():
    return "<p><a href=\"https://github.com/PYROP3\">Hello, World!</a></p>"

@bot.event
async def on_ready():
    app.logger.info(f"{bot.user} has connected to Discord")

async def _find_multi(ctx: SlashContext, users):
    msg = f"🔎 Hey {ctx.author.name}! Aqui está o resultado da minha investigação:"
    vcs = {}
    for member in users:
        found_this = False
        for vc in ctx.guild.voice_channels:
            if not found_this:
                app.logger.debug(f"Members in {vc.name} -> " + ", ".join([member.name for member in vc.members]))
                if member in vc.members:
                    app.logger.debug(f"Found mentioned user {member.name} in vc {vc.name}")
                    found_this = True
                    try:
                        vcs[vc] += [member]
                    except KeyError:
                        vcs[vc] = [member]
        if not found_this:
            app.logger.debug(f"Could not find {member.name}")
            try:
                vcs[None] += [member]
            except KeyError:
                vcs[None] = [member]
    for vc in vcs:
        if vc is not None:
            msg += "\n\t- " + ", ".join([member.name for member in vcs[vc]]) + " " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em {vc.mention}"
    if None in vcs:
        msg += "\n\t- " + ", ".join([member.name for member in vcs[vc]]) + " não " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em nenhum chat de voz"
    await ctx.send(content=msg, hidden=True)

async def _find_one(ctx, user):
    await _find_multi(ctx, [user])

def toOrdinal(n: int):
    if (n > 10 and n < 20): return f"{n}th"
    order = n % 10
    return "{}{}".format(n, ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"][order])

n_users = 25

opts = [discord_slash.manage_commands.create_option(name="user", description="1st user to find", option_type=6, required=True)]
for i in range(n_users - 1):
    opts += [discord_slash.manage_commands.create_option(name=f"additional_user{i}", description="{} user to find".format(toOrdinal(i + 2)), option_type=6, required=False)]

# Commands

@slash.slash(name="find", description="Find users in voice channels", options=opts, guild_ids=guild_ids)
async def _find(ctx: SlashContext, **kwargs):
    users = [kwargs[user] for user in kwargs if kwargs[user] is not None]
    app.logger.debug("Mentioned " + ', '.join([user.name for user in users]))
    await _find_multi(ctx, users)

@slash.context_menu(target=2, name="Find", guild_ids=guild_ids)
async def _find_contextual(ctx: SlashContext, *args, **kwargs):
    await _find_one(ctx, ctx.target_author)

Thread(target=app.run, kwargs={"host":"0.0.0.0", "port":os.getenv("PORT")}).start()

bot.run(TOKEN)
