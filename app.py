import asyncio
import discord
import os
import logging
from flask import Flask
from dotenv import load_dotenv
from threading import Thread

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = discord.Client()
app = Flask(__name__)
app.logger.root.setLevel(logging.getLevelName(os.getenv('LOG_LEVEL')))

@app.route("/")
def hello_world():
    return "<p><a href=\"https://github.com/PYROP3\">Hello, World!</a></p>"

@bot.event
async def on_ready():
    app.logger.info(f"{bot.user} has connected to Discord")

@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user:
        app.logger.info(f"Received {message.content} from {message.author} in guild {message.guild}")
        if message.content[0] == "?":
            if (len(message.mentions) > 0):
                app.logger.debug("Mentioned " + ", ".join([mention.name for mention in message.mentions]))
                msg = f"🔎 Hey {message.author.mention}, aqui está o resultado da minha investigação:"
                vcs = {}
                for member in message.mentions:
                    app.logger.debug(f"Searching for {member.name}")
                    found_this = False
                    for vc in message.guild.voice_channels:
                        if not found_this:
                            app.logger.debug(f"Members in {vc.name} -> " + ", ".join([member.name for member in vc.members]))
                            if member in vc.members:
                                app.logger.debug(f"Found mentioned user {member.mention} in vc {vc.name}")
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
                        msg += "\n\t- " + ", ".join([member.mention for member in vcs[vc]]) + " " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em {vc.mention}"
                if None in vcs:
                    msg += "\n\t- " + ", ".join([member.mention for member in vcs[vc]]) + " não " + ("está" if len(vcs[vc]) == 1 else "estão") + f" em nenhum chat de voz"
                await message.channel.send(msg)
            else:
                pass
                app.logger.info("No mentions in message")

Thread(target=app.run, kwargs={"host":"0.0.0.0", "port":os.getenv("PORT")}).start()

bot.run(TOKEN)
