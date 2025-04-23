import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from config import BOT_PREFIX, TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        from cogs.music import Music
        await self.add_cog(Music(self))

bot = MyBot(command_prefix=BOT_PREFIX, intents=intents)

from cogs.help import MyHelp
bot.help_command = MyHelp()

async def main():
    if not TOKEN:
        logger.error('Brak tokena. Ustaw zmienną środowiskową DISCORD_TOKEN lub wpisz TOKEN w config.py.')
        return
    await bot.start(TOKEN)

@bot.event
async def on_ready():
    logger.info(f'Zalogowano jako {bot.user}!')

if __name__ == '__main__':
    asyncio.run(main())
