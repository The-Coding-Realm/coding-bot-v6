from __future__ import annotations

import asyncio
import datetime as dt
import functools
import itertools
import sys
import traceback
from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable, List, Optional

import aiohttp
import discord
import humanize
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFilter, ImageFont

if TYPE_CHECKING:
    from ext.models import CodingBot


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
        img = BytesIO(await member.avatar.with_format("png").with_size(128).read())
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