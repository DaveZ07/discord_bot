import discord
from discord.ext import commands

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Pomoc', colour=discord.Colour.gold())
        for cmd in self.context.bot.commands:
            embed.add_field(name=cmd.name, value=cmd.help or 'Brak opisu', inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=f'Pomoc: {command.name}', description=command.help or 'Brak opisu', colour=discord.Colour.gold())
        await self.get_destination().send(embed=embed)
