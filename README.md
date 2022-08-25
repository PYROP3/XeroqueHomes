# XeroqueHomes

Discord bot to quickly find user(s) in voice channels

## Execution

The following environment variables must be set prior to execution:

 - `TOKEN`: Discord bot token
 - `GUILD_IDS`: Discord Guild IDs that the bot will be allowed to operate in, joined by `.`

 You may also set the `LOG_LEVEL` variable to determine the verbosity of logs (according to the `logging` python module); defaults to DEBUG.

 The available values, in order of verbosity, are:

 > CRITICAL = FATAL < ERROR < WARNING = WARN < INFO < DEBUG

### .env file

This bot utilizes load\_dotenv() to fetch the environment variables from the .env in the current directory. Such a file should be structured like so

```
DISCORD_TOKEN=<Client token specific to this bot, refer to https://discord.com/developers/applications, e.g. 0123456789abcdefABCDEF0123.456789.abcdefABCDEF0123456789abcdefABCDEF0123>
GUILD_IDS=<Guild ID where the bot will operate, e.g. 012345678901234567>
LOG_LEVEL=<Log level as described above, e.g. INFO>
```

Note that these variables can also be set in other ways (such as CLI or the hosting service dashboard), but using `.env` can be useful in cases of self-hosting. 
### Run

Then you can execute the bot standalone using

 ```sh
python3 xeroque.py
 ```

You can also use [Bismuth](https://github.com/PYROP3/Bismuth) in order to execute the bot automatically.

## Usage

The bot can find users via the usage of slash commands, supporting up to 25 users in a single command:

```
/find [@user]{1,25}
```

The bot also supports contextual commands: just right-click the user you wish to locate > `Apps` > `Find`
