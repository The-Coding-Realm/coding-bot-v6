import asyncio
import datetime as dt
import functools
import sys
import traceback
from io import BytesIO

import discord
import humanize
from PIL import Image, ImageDraw, ImageFilter, ImageFont


async def log_error(bot, event_method, *args, **kwargs):
    channel = bot.get_channel(826861610173333595)
    try:
        title = 'Ignoring exception in {}'.format(event_method)
        err = ''.join(traceback.format_exc())
        embed = discord.Embed(title=title, description=f'```py\n{err}```',
                              timestamp=dt.datetime.now(dt.timezone.utc),
                              color=discord.Color.red())
        await channel.send(embed=embed)
    except discord.errors.Forbidden:
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()


def executor():
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            loop = asyncio.get_event_loop()
            thing = functools.partial(func, *args, **kwargs)
            return loop.run_in_executor(None, thing)
        return inner
    return outer


class WelcomeBanner:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.font = {
            12: ImageFont.truetype("./storage/fonts/Poppins/Poppins-Bold.ttf", size=12),
            15: ImageFont.truetype("./storage/fonts/Poppins/Poppins-Bold.ttf", size=15),
            25: ImageFont.truetype("./storage/fonts/Poppins/Poppins-Bold.ttf", size=25),
        }

    @executor()
    def generate_image(self, **kwargs) -> discord.File:
        inviter = kwargs.get('inviter')
        vanity = kwargs.get('vanity')
        inv = kwargs.get('inv')
        member = kwargs.get('member')
        profile_picture = kwargs.pop('pfp')
        banner = kwargs.pop('banner')
        ago = kwargs.pop('ago')
        base = Image.open(profile_picture).convert("RGBA").resize((128, 128))
        txt = Image.open(banner).convert("RGBA")
        txt = txt.point(lambda p: int(p * 0.5))
        txt = txt.resize((512, 200))
        draw = ImageDraw.Draw(txt)
        fill = (255, 255, 255, 255)
        text = "Welcome to The Coding Realm"
        text_width, text_height = draw.textsize(text, self.font.get(25))
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

    async def construct_image(self, **kwargs) -> discord.File:
        member = kwargs.pop('member')
        inviter = await self.bot.tracker.fetch_inviter(member)
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
        except:
            banner = './storage/banner.png'

        file = await self.generate_image(
            inviter=inviter,
            vanity=vanity,
            inv=inv,
            member=member,
            pfp=img,
            banner=banner,
            ago=ago
        )
        return file
