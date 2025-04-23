import asyncio
import yt_dlp
import discord
from discord.ext import commands
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from config import YTDL_OPTIONS

@dataclass
class Track:
    title: str
    url: str
    thumbnail: Optional[str] = None

@dataclass
class GuildMusic:
    queue: asyncio.Queue                    = field(default_factory=asyncio.Queue)
    current: Optional[Track]                = None
    voice_client: Optional[discord.VoiceClient] = None
    playing: bool                           = False
    playlist_titles: List[str]              = field(default_factory=list)
    playlist_urls: List[str]                = field(default_factory=list)
    playlist_thumbnails: List[Optional[str]] = field(default_factory=list)

async def send_embed(ctx, title: str, description: str, color: discord.Colour, thumbnail: Optional[str] = None):
    embed = discord.Embed(title=title, description=description, colour=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    await ctx.send(embed=embed)

async def extract_info(url: str) -> Track:
    loop = asyncio.get_event_loop()
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    if 'entries' in data and data['entries']:
        data = data['entries'][0]
    return Track(
        title=data.get('title'),
        url=data.get('url'),
        thumbnail=(data.get('thumbnail') if data.get('thumbnail','').startswith('http') else None)
    )

async def extract_playlist(url: str):
    opts = {**YTDL_OPTIONS, 'extract_flat': True, 'ignoreerrors': True, 'quiet': True}
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
    entries = data.get('entries') or []
    titles, urls, thumbs = [], [], []
    for entry in entries:
        if not entry:
            continue
        titles.append(entry.get('title'))
        urls.append(entry.get('url'))
        t = entry.get('thumbnail')
        thumbs.append(t if t and t.startswith('http') else None)
    return titles, urls, thumbs

class SearchView(discord.ui.View):
    def __init__(self, entries: List[dict], guild_data: GuildMusic, ctx: commands.Context):
        super().__init__(timeout=60)
        self.entries = entries
        self.guild_data = guild_data
        self.ctx = ctx
        for i in range(min(10, len(entries))):
            btn = discord.ui.Button(
                label=str(i+1),
                style=discord.ButtonStyle.primary,
                custom_id=f'search_{i}'
            )
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, idx: int):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer() 
            
            entry = self.entries[idx]
            vid = entry.get('id') or entry.get('url')
            url = f'https://www.youtube.com/watch?v={vid}'
            track = await extract_info(url)
            await self.guild_data.queue.put(track)

            if not self.guild_data.playing:
                self.ctx.bot.loop.create_task(self.ctx.cog.player_loop(interaction.guild_id, self.ctx))
            
            await interaction.message.edit(
                content=f'Dodano do kolejki: 🎵 {track.title}',
                embed=None,
                view=None
            )
        return callback

    @discord.ui.button(label='⏹️', style=discord.ButtonStyle.danger, custom_id='search_cancel')
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content='Anulowano wyszukiwanie.', embed=None, view=None)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds: Dict[int, GuildMusic] = {}

    def get_data(self, guild_id: int) -> GuildMusic:
        return self.guilds.setdefault(guild_id, GuildMusic())

    async def ensure_voice(self, ctx) -> Optional[discord.VoiceClient]:
        data = self.get_data(ctx.guild.id)
        if data.voice_client and data.voice_client.is_connected():
            return data.voice_client
        if not ctx.author.voice:
            await send_embed(ctx, 'Błąd', 'Musisz być na kanale głosowym', discord.Colour.red())
            return None
        data.voice_client = await ctx.author.voice.channel.connect()
        return data.voice_client

    async def player_loop(self, guild_id: int, ctx):
        data = self.get_data(guild_id)
        while True:
            track = await data.queue.get()
            data.current = track
            data.playing = True
            data.voice_client.play(
                discord.FFmpegPCMAudio(
                    track.url,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn'
                ),
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self._after_play(guild_id), self.bot.loop
                )
            )
            await send_embed(ctx, 'Odtwarzam', f'🎵 {track.title}', discord.Colour.blue(), thumbnail=track.thumbnail)
            while data.voice_client.is_playing() or data.voice_client.is_paused():
                await asyncio.sleep(1)
            data.queue.task_done()

    async def _after_play(self, guild_id: int):
        self.guilds[guild_id].playing = False

    @commands.command(name='search', help='Wyszukaj utwory: !search <fraza>')
    async def search(self, ctx, *, query: str):
        data = self.get_data(ctx.guild.id)
        if not await self.ensure_voice(ctx):
            return
        opts = {**YTDL_OPTIONS, 'default_search': 'ytsearch10', 'extract_flat': True, 'ignoreerrors': True, 'quiet': True}
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch10:{query}", download=False))
        entries = info.get('entries') or []
        if not entries:
            await send_embed(ctx, 'Błąd', 'Nie znaleziono wyników', discord.Colour.red())
            return
        embed = discord.Embed(
            title=f'Wyniki wyszukiwania dla: {query}',
            colour=discord.Colour.blue()
        )
        embed.description = '\n'.join(
            f"{i+1}. {e.get('title','Brak tytułu')}"
            for i,e in enumerate(entries[:10])
        )
        view = SearchView(entries, data, ctx)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='play', help='Odtwórz utwór lub playlistę: !play <fraza> lub <URL>')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def play(self, ctx, *, query: str):
        voice = await self.ensure_voice(ctx)
        if not voice:
            return
        data = self.get_data(ctx.guild.id)
        if 'playlist?list=' in query or '&list=' in query:
            titles, urls, thumbs = await extract_playlist(query)
            if not urls:
                await send_embed(ctx, 'Błąd', 'Nie można załadować playlisty', discord.Colour.red())
                return
            data.playlist_titles, data.playlist_urls, data.playlist_thumbnails = titles, urls, thumbs
            for url in urls:
                await data.queue.put(await extract_info(url))
            await send_embed(ctx, 'Playlista', f'Dodano {len(urls)} utworów do kolejki', discord.Colour.green())
            if not data.playing:
                self.bot.loop.create_task(self.player_loop(ctx.guild.id, ctx))
        else:
            track = await extract_info(query)
            await data.queue.put(track)
            if data.playing:
                await send_embed(ctx, 'Dodano do kolejki', f'🎵 {track.title}', discord.Colour.green())
            else:
                self.bot.loop.create_task(self.player_loop(ctx.guild.id, ctx))

    @commands.command(name='next', help='Pomiń aktualny utwór')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def next(self, ctx):
        data = self.get_data(ctx.guild.id)
        if data.voice_client and data.voice_client.is_playing():
            data.voice_client.stop()
            await send_embed(ctx, 'Pominięto', 'Przechodzę do następnego utworu', discord.Colour.orange())
        else:
            await send_embed(ctx, 'Błąd', 'Brak odtwarzania', discord.Colour.red())

    @commands.command(name='disconnect', help='Rozłącza bota z kanału głosowego')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def disconnect(self, ctx):
        data = self.get_data(ctx.guild.id)
        if data.voice_client:
            data.queue = asyncio.Queue()
            data.playlist_titles.clear()
            data.playlist_urls.clear()
            data.playlist_thumbnails.clear()
            data.voice_client.stop()
            await data.voice_client.disconnect()
            data.voice_client = None
            data.playing = False
            await send_embed(ctx, 'Disconnected', 'Bot rozłączony i kolejka wyczyszczona', discord.Colour.red())
        else:
            await send_embed(ctx, 'Błąd', 'Bot nie jest połączony z kanałem', discord.Colour.red())

    @commands.command(name='pause', help='Zapauzuj aktualnie odtwarzany utwór')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def pause(self, ctx):
        data = self.get_data(ctx.guild.id)
        if data.voice_client and data.voice_client.is_playing():
            data.voice_client.pause()
            await send_embed(ctx, 'Pauza', 'Odtwarzanie zapauzowane', discord.Colour.blue())
        else:
            await send_embed(ctx, 'Błąd', 'Brak odtwarzania', discord.Colour.red())

    @commands.command(name='continue', help='Wznów odtwarzanie')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def _continue(self, ctx):
        data = self.get_data(ctx.guild.id)
        if data.voice_client and data.voice_client.is_paused():
            data.voice_client.resume()
            await send_embed(ctx, 'Wznawianie', 'Odtwarzanie wznowione', discord.Colour.green())
        else:
            await send_embed(ctx, 'Błąd', 'Brak zapauzowanego utworu', discord.Colour.red())

    @commands.command(name='list', help='Pokazuje utwory z ostatniej playlisty')
    async def list(self, ctx):
        data = self.get_data(ctx.guild.id)
        if not data.playlist_titles:
            await send_embed(ctx, 'Błąd', 'Brak załadowanej playlisty', discord.Colour.red())
            return
        desc = '\n'.join(f'{i+1}. {t}' for i,t in enumerate(data.playlist_titles))
        await send_embed(ctx, 'Playlista', desc, discord.Colour.blue())

    @commands.command(name='select', help='Wybiera utwór z playlisty: !select <numer>')
    async def select(self, ctx, number: int):
        data = self.get_data(ctx.guild.id)
        if not data.playlist_urls:
            await send_embed(ctx, 'Błąd', 'Brak załadowanej playlisty', discord.Colour.red())
            return
        idx = number - 1
        if not (0 <= idx < len(data.playlist_urls)):
            await send_embed(ctx, 'Błąd', f'Podaj numer od 1 do {len(data.playlist_urls)}', discord.Colour.red())
            return
        track = await extract_info(data.playlist_urls[idx])
        await data.queue.put(track)
        await send_embed(ctx, 'Dodano do kolejki', f'🎵 {track.title}', discord.Colour.green())

def setup(bot):
    bot.add_cog(Music(bot))
