from __future__ import annotations

import asyncio
import base64
import datetime as dt
import functools
import itertools
import re
import string
import sys
import traceback
import urllib
from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple

import aiohttp
import discord
import humanize
from bs4 import BeautifulSoup
from colorthief import ColorThief
from discord.ext import tasks
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ext.consts import TCR_STAFF_ROLE_ID

if TYPE_CHECKING:
    from ext.models import CodingBot


async def check_invite(bot, content, channel):
    # content = discord.utils.remove_markdown(content)

    whitelisted = [
                    681882711945641997,  # TCA
                    336642139381301249,  # Discord.py
                    222078108977594368,  # Discord.js
                    881207955029110855,  # Pycord
                    267624335836053506,  # Python
                    412754940885467146,  # Blurple
                    613425648685547541,  # Discord Developers
    ]
    pattern = (
        r'discord(?:(?:(?:app)?\.com)\/invite|\.gg)/([a-zA-z0-9\-]{2,})\b')
    matches = re.findall(pattern, content, re.MULTILINE)
    if channel.id in [
        754992725480439809, # self-advertising
        727029474767667322, # partnerships
    ]:
        return False
    if len(matches) > 5: # why 5?
        return True
    for code in matches:
        try:
            invite = await bot.fetch_invite(code)
        except discord.errors.NotFound:
            invite = None
        if invite:
            if invite.guild.id not in whitelisted:
                return True
    return False


async def find_anime_source(session, source_image: str):
    base = "https://api.trace.moe/search?anilistInfo&url={}"
    async with session.get(base.format(source_image)) as resp:
        data = await resp.json()
    return data

def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk

def ordinal_suffix_of(i):
    if i % 100 // 10 != 1:
        if i % 10 == 1:
            return 'st'
        elif i % 10 == 2:
            return 'nd'
        elif i % 10 == 3:
            return 'rd'
    return 'th'


async def log_error(bot: CodingBot, event_method: str, *args: Any, **kwargs: Any):
    channel = bot.get_channel(826861610173333595)
    try:
        title = 'Ignoring exception in {}'.format(event_method)
        err = ''.join(traceback.format_exc())
        embed = discord.Embed(title=title, description=f'```py\n{err}```',
                              timestamp=dt.datetime.now(dt.timezone.utc),
                              color=discord.Color.red())

        # channel is always a Messageable
        await channel.send(embed=embed)  # type: ignore
    except (discord.errors.Forbidden, AttributeError):
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()


def executor() -> Callable[[Callable[..., Any]], Any]:
    def outer(func: Callable[..., Any]):
        @functools.wraps(func)
        def inner(*args: Any, **kwargs: Any):
            loop = asyncio.get_event_loop()
            thing = functools.partial(func, *args, **kwargs)
            return loop.run_in_executor(None, thing)
        return inner
    return outer


@executor()
def create_trash_meme(
    member_avatar: BytesIO,
    author_avatar: BytesIO
) -> discord.File:
    image = Image.open('./storage/Trash.png')
    background = Image.new('RGBA', image.size, color=(255, 255, 255, 0))

    avatar_one = author_avatar
    avatar_two = member_avatar

    avatar_one_image = Image.open(avatar_one).resize((180, 180))
    avatar_two_image = Image.open(avatar_two).resize(
        (180, 180)).rotate(5, expand=True)

    background.paste(avatar_one_image, (100, 190))
    background.paste(avatar_two_image, (372, 77))
    background.paste(image, (0, 0), image)

    buffer = BytesIO()
    background.save(buffer, format='PNG')
    buffer.seek(0)
    file = discord.File(buffer, filename='Trash.png')

    return file


class WelcomeBanner:
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot
        self.font = {
            12: ImageFont.truetype("./storage/fonts/Poppins/Poppins-Bold.ttf", size=12),
            15: ImageFont.truetype("./storage/fonts/Poppins/Poppins-Bold.ttf", size=15),
            25: ImageFont.truetype("./storage/fonts/Poppins/Poppins-Bold.ttf", size=25),
        }

    @executor()
    def generate_image(self, member: discord.Member, **kwargs: Any) -> discord.File:
        inviter = kwargs.get('inviter')
        vanity = kwargs.get('vanity')
        inv = kwargs.get('inv')
        profile_picture = kwargs.pop('pfp')
        banner = kwargs.pop('banner')
        ago = kwargs.pop('ago')
        base = Image.open(profile_picture).convert("RGBA").resize((128, 128))
        txt = Image.open(banner).convert("RGBA")
        txt = txt.point(lambda p: int(p * 0.5))  # type: ignore
        txt = txt.resize((512, 200))
        draw = ImageDraw.Draw(txt)
        fill = (255, 255, 255, 255)
        text = "Welcome to The Coding Realm"
        text_width, _ = draw.textsize(text, self.font.get(25))
        width_height = ((txt.size[0] - text_width) //
                        2, (txt.size[1] // 31) * 1)
        draw.text(width_height, text, font=self.font.get(
            25), fill=fill, align='center')
        text = str(member)
        calculation = ((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 4)
        draw.text(calculation, text, font=self.font.get(
            15), fill=fill, align='center')
        text = f"ID: {member.id}"
        calculation = ((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 6)
        draw.text(calculation, text, font=self.font.get(
            12), fill=fill, align='center')
        if inviter:
            text = f'• Invited by: {inviter}'
            draw.text(((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 9),
                      text, font=self.font.get(12), fill=fill, align='center')
            text = f'• ID: {inviter.id}, Invites: {inv}'
            draw.text(((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 11),
                      text, font=self.font.get(12), fill=fill, align='center')
            text = f'• Account created: {humanize.naturaldelta(ago)} ago'
            draw.text(((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 13),
                      text, font=self.font.get(12), fill=fill, align='center')
        else:
            if vanity:
                invite = vanity
                if len(invite.code) > 7:
                    invite.code = f'{invite.code[:7]}...'
                text = f'• Joined using vanity invite: {invite.code} ({invite.uses} uses)'
            else:
                text = 'I couldn\'t find who invited them'
            draw.text(((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 9),
                      text, font=self.font.get(12), fill=fill, align='center')
            text = f'• Account created: {humanize.naturaldelta(ago)} ago'
            draw.text(((txt.size[0] // 8) * 3, (txt.size[1] // 16) * 11),
                      text, font=self.font.get(12), fill=fill, align='center')
        blur_radius = 1
        offset = 0
        offset = blur_radius * 2 + offset
        mask = Image.new("L", base.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse(
            (offset, offset, base.size[0] - offset, base.size[1] - offset), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
        txt.paste(base, (base.size[0] // 4, (base.size[1] // 8) * 3), mask)
        buf = BytesIO()
        txt.save(buf, format='png')
        buf.seek(0)
        file = discord.File(buf, filename='welcome.png')
        return file

    async def construct_image(self, **kwargs: Any) -> discord.File:
        member = kwargs.pop('member')
        inviter: Optional[discord.Member] = await self.bot.tracker.fetch_inviter(member)
        inv = None
        vanity = None
        if inviter:
            inv = sum(i.uses for i in (await member.guild.invites()) if i.inviter
                      and i.inviter.id == inviter.id)
        else:
            try:
                vanity = await member.guild.vanity_invite()
            except:
                pass
        ago = dt.datetime.now(dt.timezone.utc) - member.created_at
        img = BytesIO(await member.display_avatar.with_format("png").with_size(128).read())
        try:
            banner = BytesIO(await member.guild.banner.with_format("png").with_size(512).read())
        except AttributeError:
            banner = './storage/banner.png'

        file = await self.generate_image(
            member,
            inviter=inviter,
            vanity=vanity,
            inv=inv,
            pfp=img,
            banner=banner,
            ago=ago
        )
        return file


class UrbanDefinition:
    
    __slots__ = ('meaning', 'example', 'author')
    def __init__(self, meaning: str, example: str, author: str) -> None:
        self.meaning = meaning
        self.example = example
        self.author = author

    @classmethod
    def from_tuple(cls, tuple: tuple) -> 'UrbanDefinition':
        """
        Class method to convert a tuple to a UrbanDefinition object.

        Parameters
        ----------
        tuple: tuple
            The tuple to convert.

        Returns
        -------
        UrbanDefinition
            The UrbanDefinition object.
        """
        return cls(*tuple)

class UrbanDictionary:

    BASE_URL = "https://www.urbandictionary.com"
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session

    def require_session(coro: Callable) -> None:
        """
        Outer decorator for methods that require a session.

        Parameters
        ----------
        coro : `Callable`
            The coroutine to be wrapped.
        
        Returns
        -------
        `Callable`
            The wrapped coroutine.
        """
        async def wrapper(self, *args):
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()
            return await coro(self, *args)
        return wrapper

    async def __aenter__(self) -> 'UrbanDictionary':
        return self

    async def __aexit__(self, *exc) -> None:
        await self.session.close()

    def get_example(self, soup: BeautifulSoup, references: list) -> str:
        """
        Responsible for getting the example from the soup.
        
        Parameters
        ----------
        soup : BeautifulSoup
            The soup to get the example from.
        references : list
            The list of references to the example.

        Returns
        -------
        str
            The example.
        """
        final_examples = []
        examples = soup.find_all('div', {'class', 'example'})
        examples = [example.text for example in examples]
        for example in examples:
            final_example = example
            for key, value in references:
                if key not in final_example:
                    if final_example not in final_examples:
                        final_examples.append(final_example)
                        continue
                final_example = final_example.replace(key, f"[{key}]({self.BASE_URL}{value})")
        return final_examples

    def get_meanings(self, soup: BeautifulSoup, references: list, autolinks: list) -> list:
        """
        Responsible for getting the meanings of the word

        Parameters
        ----------
        soup: BeautifulSoup
            The soup of the page
        references: list
            A list of tuples containing the key and value of the references
        autolinks: list
            A list of tuples containing the key and value of the autolinks
        
        Returns
        -------
        list
            A list of meanings
        """
        final_meanings = []

        meanings = soup.find_all('div', {'class', 'meaning'})
        meanings = [meaning.text for meaning in meanings]
        references = [(autolink.text, autolink["href"]) for autolink in autolinks]

        for meaning in meanings:
            final_meaning = meaning
            for key, value in references:
                if key not in final_meaning:
                    if final_meaning not in final_meanings:
                        continue
                final_meaning = final_meaning.replace(key, f"[{key}]({self.BASE_URL}{value})")
            final_meanings.append(final_meaning)
        return final_meanings

    def get_authors(self, soup: BeautifulSoup) -> dict:
        authors = soup.find_all('div', {'class', 'contributor'})
        authors = {author.text: f"{self.BASE_URL}{author.find('a')['href']}" for author in authors}
        return authors

    @executor()
    def parse(self, html: str, results: int) -> List[UrbanDefinition]:
        """
        Responsible for parsing the html and returning a list of UrbanDefinitions
        
        Parameters
        ----------
        html: str
            The html to parse
        results: int
            The amount of results to return
        
        Returns
        -------
        List[UrbanDefinition]
            A list of UrbanDefinitions
        """
        soup = BeautifulSoup(html, 'lxml')
        autolinks = soup.find_all('a', {'class', 'autolink'})
        references = [(autolink.text, autolink["href"]) for autolink in autolinks]
        final_meanings = self.get_meanings(soup, references, autolinks)
        final_examples = self.get_example(soup, references)
        authors = self.get_authors(soup)
        final_meanings = final_meanings
        final_examples = final_examples
        authors = authors
        return [
            UrbanDefinition(meaning, example, author) 
            for (meaning, example, author) in 
            zip(final_meanings, final_examples, authors)
        ]

    @require_session
    async def define(self, word: str, results: int = 1) -> List[UrbanDefinition]:
        """
        Get the definition of a word from urban dictionary.

        Parameters
        ----------
        word : str
            The word to define.
        results : int   
            The number of results to return.
        
        Returns
        -------
        List[UrbanDefinition]
            A list of UrbanDefinition objects.

        Raises
        ------
        Exception
            If the word is not found.
        """
        real_link = f"{self.BASE_URL}/define.php?term={word}"
        async with self.session.get(real_link) as resp:
            if resp.status != 200:
                raise Exception("Failed to get definition")
            else:
               text = await resp.text()
        result = await self.parse(text, results)
        return result

class Spotify:
    __slots__ = ('member', 'bot', 'embed', 'regex', 'headers', 'counter')
    
    def __init__(self, *, bot, member) -> None:
        """
        Class that represents a Spotify object, used for creating listening embeds
        Parameters:
        ----------------
        bot : commands.Bot
            represents the Bot object
        member : discord.Member
            represents the Member object whose spotify listening is to be handled
        """
        self.member = member
        self.bot = bot
        self.embed = discord.Embed(
            title=f"{member.display_name} is Listening to Spotify", 
            color=discord.Color.green()
        )
        self.counter = 0

    async def request_pass(self, *, track_id: str):
        """
        Requests for a list of artists from the spotify API
        Parameters:
        ----------------
            track_id : str
                Spotify track's id
        Returns
        ----------------
        list
            A list of artist details
        Raises
        ----------------
        Exception
            If Spotify API is down
        """
        try:
            headers = {"Authorization":
                           f'Basic {base64.urlsafe_b64encode(f"{self.bot.spotify_client_id.strip()}:{self.bot.spotify_client_secret.strip()}".encode()).decode()}',
                       "Content-Type":
                           "application/x-www-form-urlencoded", }
            params = {"grant_type": "client_credentials"}
            if not self.bot.spotify_session or dt.datetime.utcnow() > self.bot.spotify_session[1]:
                resp = await self.bot.session.post("https://accounts.spotify.com/api/token",
                                                   params=params, headers=headers)
                auth_js = await resp.json()
                timenow = dt.datetime.utcnow() + dt.timedelta(seconds=auth_js['expires_in'])
                type_token = auth_js['token_type']
                token = auth_js['access_token']
                auth_token = f"{type_token} {token}"
                self.bot.spotify_session = (auth_token, timenow)
            else:
                auth_token = self.bot.spotify_session[0]
        except Exception:
            raise Exception("Something went wrong!")
        else:
            try:
                resp = await self.bot.session.get(
                    f"https://api.spotify.com/v1/tracks/{urllib.parse.quote(track_id)}",
                    params={"market": "US"},
                    headers={"Authorization": auth_token},
                )
                json = await resp.json()
                return json
            except Exception:
                if self.counter == 4:
                    raise Exception("Something went wrong!")
                else:
                    self.counter += 1
                    await self.request_pass(track_id=track_id)

    @staticmethod
    @executor()
    def pil_process(pic, name, artists, time, time_at, track) -> discord.File:
        """
        Makes an image with spotify album cover with Pillow
        
        Parameters:
        ----------------
        pic : BytesIO
            BytesIO object of the album cover
        name : str
            Name of the song
        artists : list
            Name(s) of the Artists
        time : int
            Total duration of song in seconds
        time_at : int
            Total duration into the song in seconds
        track : int
            Offset for covering the played bar portion
        Returns
        ----------------
        discord.File
            contains the spotify image
        """
        s = ColorThief(pic)
        color = s.get_palette(color_count=2)
        result = Image.new('RGBA', (575, 170))
        draw = ImageDraw.Draw(result)
        color_font = "white" if sum(color[0]) < 450 else "black"
        draw.rounded_rectangle(((0, 0), (575, 170)), 20, fill=color[0])
        s = Image.open(pic)
        s = s.resize((128, 128))
        result1 = Image.new('RGBA', (129, 128))
        Image.Image.paste(result, result1, (29, 23))
        Image.Image.paste(result, s, (27, 20))
        font = ImageFont.truetype("storage/fonts/spotify.ttf", 28)
        font2 = ImageFont.truetype("storage/fonts/spotify.ttf", 18)
        draw.text((170, 20), name, color_font, font=font)
        draw.text((170, 55), artists, color_font, font=font2)
        draw.text((500, 120), time, color_font, font=font2)
        draw.text((170, 120), time_at, color_font, font=font2)
        draw.rectangle(((230, 130), (490, 127)), fill="grey")  # play bar
        draw.rectangle(((230, 130), (230 + track, 127)), fill=color_font)
        draw.ellipse((230 + track - 5, 122, 230 + track + 5, 134), fill=color_font, outline=color_font)
        draw.ellipse((230 + track - 6, 122, 230 + track + 6, 134), fill=color_font, outline=color_font)
        output = BytesIO()
        result.save(output, "png")
        output.seek(0)
        return discord.File(fp=output, filename="spotify.png")

    async def get_from_local(self, bot, act: discord.Spotify) -> discord.File:
        """
        Makes an image with spotify album cover with Pillow
        
        Parameters:
        ----------------
        bot : commands.Bot
            represents our Bot object
        act : discord.Spotify
            activity object to get information from
        Returns
        ----------------
        discord.File
            contains the spotify image
        """
        s = tuple(f"{string.ascii_letters}{string.digits}{string.punctuation} ")
        artists = ', '.join(act.artists)
        artists = ''.join([x for x in artists if x in s])
        artists = artists[0:36] + "..." if len(artists) > 36 else artists
        time = act.duration.seconds
        time_at = (dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) - act.start).total_seconds()
        track = (time_at / time) * 260
        time = f"{time // 60:02d}:{time % 60:02d}"
        time_at = f"{int((time_at if time_at > 0 else 0) // 60):02d}:{int((time_at if time_at > 0 else 0) % 60):02d}"
        pog = act.album_cover_url
        name = ''.join([x for x in act.title if x in s])
        name = name[0:21] + "..." if len(name) > 21 else name
        rad = await bot.session.get(pog)
        pic = BytesIO(await rad.read())
        return await self.pil_process(pic, name, artists, time, time_at, track)

    async def get_embed(self) -> Tuple[discord.Embed, discord.File, discord.ui.View]:
        """
        Creates the Embed object
        
        Returns
        ----------------
        Tuple[discord.Embed, discord.File]
            the embed object and the file with spotify image
        """
        activity = discord.utils.find(lambda activity: isinstance(activity, discord.Spotify), self.member.activities)
        if not activity:
            return False
        result = await self.request_pass(track_id=activity.track_id)
        final_string = ', '.join(
            [f"[{resp['name']}]({resp['external_urls']['spotify']})" for resp in result['artists']]
        )
        url = activity.track_url
        image = await self.get_from_local(self.bot, activity)
        self.embed.description = f"**Artists**: {final_string}\n**Album**: [{activity.album}]({url})"
        self.embed.set_image(url="attachment://spotify.png")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(url=url, style=discord.ButtonStyle.green, label="\u2007Open in Spotify", emoji="<:spotify:983984483755765790>"))
        return (self.embed, image, view)

async def get_rock(self):
    rock = await self.http.api["rock"]["random"]()
    name = rock["name"]
    desc = rock["desc"]
    image = rock["image"]
    rating = rock["rating"]
    embed = await self.bot.embed(
        title=f"🪨   {name}",
        url=image or "https://www.youtube.com/watch?v=o-YBDTqX_ZU",
        description=f"```yaml\n{desc}```",
    )
    if image is not None and image != "none" and image != "":
        embed.set_thumbnail(url=image)
    return (embed, rating)

class AntiRaid:
    """
    AntiRaid class
    """

    def __init__(self, bot):
        self.possible_raid = False
        self.possible_raid_enabled_at = None
        self.bot: CodingBot = bot
        self.cache: set[discord.Member] = set()
        self.raid_mode_criteria: int = None

    def check(self, member: discord.Member):
        """
        Checks if the member is in the cache
        
        Parameters:

        """
        if (discord.utils.utcnow() - member.created_at).days in range(self.raid_mode_criteria - 1, self.raid_mode_criteria + 1):
            return True

    async def cache_insert_or_ban(self, member: discord.Member) -> bool:
        """
        Checks if the member is in the cache
        
        Parameters:
        ----------------
        member : discord.Member
            member to check
        """
        if not self.bot.raid_mode_enabled:
            self.cache.add(member)
            print(self.cache)
            return False
        else:
            if self.check(member):
                await member.ban(reason="Raid mode checks met")
                return True
            else:
                channel = self.bot.get_channel(984420447401676811)
                assert channel is not None

                await channel.send(f"{member.mention} is highly unlikely to be part of the raid, skipping user.\nReason: Failed the raid mode checks")
                return False
    
    async def notify_staff(self) -> None:
        """
        Notifies the staff about the raid mode
        """
        channel = self.bot.get_channel(984420447401676811) # actual: 735864475994816576 test: 964165082437263361
        embed = discord.Embed(description="", title="A possible raid has been detected!", color=discord.Color.gold())
        embed.description += f"""\nThe criteria is detected to be `{self.raid_mode_criteria} ± 1` days
            Use `{self.bot.command_prefix[0]}raid-mode enable` after making sure this is not a false positive to enable raid mode!
            Upon usage of the command, the bot will automatically ban users who have been created within this time.
        """
        await channel.send(
            f"<@&{TCR_STAFF_ROLE_ID}>",
            embed=embed,

        )
            
    @tasks.loop(seconds=20)
    async def check_for_raid(self):
        """
        Checks if the member is in the cache
        
        Parameters:
        ----------------
        member : discord.Member
            member to check
        """
        if not self.bot.raid_mode_enabled:
            if self.possible_raid or not self.cache:
                return
            time_join_day = [(discord.utils.utcnow() - member.created_at).days for member in self.cache]
            min_days = min(time_join_day)
            if len([x for x in time_join_day if x in range(min_days - 1, min_days + 1)]) >= 4:
                self.raid_mode_criteria = min_days
                self.possible_raid = True
                return await self.notify_staff()
            self.cache.clear()

