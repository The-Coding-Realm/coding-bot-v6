import aiohttp
from discord.ext import tasks


class Http:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.cache = {"piston": {}}
        self.api = {
            # //////////////////////////////////////////////////////////////////////////////////////
            # prelude
            "get": {
                "meme": lambda: self.api["meme-api"]["gimme"](),
            },
            # //////////////////////////////////////////////////////////////////////////////////////
            "rock": {
                "random": lambda: self.get("https://rockapi.apiworks.tech/rock/random", _json=True),
                "top": lambda: self.get("https://rockapi.apiworks.tech/rock/top"),
            },
            "numbers": {
                "random": lambda _type="trivia": self.api["numbers"]["random_"+_type](),
                "number": lambda _type="trivia": self.api["numbers"][_type](),
                "random_trivia": lambda: self.get("http://numbersapi.com/random/trivia"),
                "random_math": lambda: self.get("http://numbersapi.com/random/math"),
                "random_date": lambda: self.get("http://numbersapi.com/random/date"),
                "random_year": lambda: self.get("http://numbersapi.com/random/year"),
                "date": lambda date: self.get(f"http://numbersapi.com/{date}/date"),
                "year": lambda year: self.get(f"http://numbersapi.com/{year}/year"),
                "trivia": lambda num: self.get(f"http://numbersapi.com/{num}"),
                "math": lambda num: self.get(f"http://numbersapi.com/{num}/math"),
            },
            "piston": {
                "runtimes": lambda: self.get("https://emkc.org/api/v2/piston/runtimes", _json=True),
                # "execute": "https://emkc.org/api/v2/piston/execute",
                "execute": lambda language, code: self.post(
                    "https://emkc.org/api/v1/piston/execute",
                    _json=True,
                    data={"language": language, "source": code}
                ),
            },
            "meme-api": {
                "gimme": lambda: self.get("https://meme-api.com/gimme/", _json=True)
            },
            "some-random-api": {
                "bottoken": lambda: self.get("https://some-random-api.ml/bottoken", _json=True),
                "animal": lambda animal: self.get(f"https://some-random-api.ml/animal/{animal}"),
                "binary-encode": lambda string: self.get(f"https://some-random-api.ml/binary?encode={string}"),
                "binary-decode": lambda binary: self.get(f"https://some-random-api.ml/binary?decode={binary}"),
                "lyrics": lambda query: self.get(f"https://some-random-api.ml/lyrics?title={query}"),
                "joke": lambda: self.get("https://some-random-api.ml/joke", _json=True),
                "filters":{
                    "invert": lambda pfp: f"https://some-random-api.ml/canvas/invert?avatar={pfp}",
                    "greyscale": lambda pfp: f"https://some-random-api.ml/canvas/greyscale?avatar={pfp}",
                    "colour": lambda pfp, hex_code: f"https://some-random-api.ml/canvas/color?avatar={pfp}&color={hex_code}",
                    "brightness": lambda pfp: f"https://some-random-api.ml/canvas/brightness?avatar={pfp}",
                    "threshold": lambda pfp: f"https://some-random-api.ml/canvas/threshold?avatar={pfp}",
                }
            },
            "joke": {
                "api": lambda: self.get("https://v2.jokeapi.dev/joke/Programming", _json=True),
            }
        }

        # self.update_data.start()

    @tasks.loop(minutes=5)
    async def update_data(self):
        self.cache["piston"]["runtimes"] = await self.get("https://emkc.org/api/v2/piston/runtimes", _json=True)

    # #/////////////////////////////////////////////////////////////////////////
    # # some-random-api
    # #/////////////////////////////////////////////////////////////////////////

    # async def get_bottoken(self):
    #     return await self.get(
    #         _url=self.api["some-random-api"]["bottoken"],
    #         _json=True
    #     )

    # #/////////////////////////////////////////////////////////////////////////
    # # meme-api
    # #/////////////////////////////////////////////////////////////////////////

    # async def get_meme(self):
    #     return await self.get(
    #         _url=self.api["meme-api"]["gimme"],
    #         _json=True
    #     )

    # #/////////////////////////////////////////////////////////////////////////
    # # 🪨 api
    # #/////////////////////////////////////////////////////////////////////////

    # async def get_random_rock(self):
    #     return await self.get(
    #         _url=self.api["rock"]["random"],
    #         _json=True
    #     )

    # async def get_top_rock(self):
    #     return await self.get(
    #         _url=self.api["rock"]["top"],
    #         _json=True
    #     )

    # #/////////////////////////////////////////////////////////////////////////
    # # numbers-api
    # #/////////////////////////////////////////////////////////////////////////

    # async def get_random_number(self, type="trivia"):
    #     return await self.get(
    #         _url=self.api["numbers"]["random_" + type]
    #     )

    # async def get_number(self, num, type="trivia"):
    #     return await self.get(
    #         _url=self.api["numbers"][type](num)
    #     )

    # #/////////////////////////////////////////////////////////////////////////
    # # piston-api
    # #/////////////////////////////////////////////////////////////////////////

    # async def get_runtimes(self):
    #     return await self.get(
    #         _url=self.api["piston"]["runtimes"],
    #         _json=True
    #     )

    # async def execute_code(self, language, code):
    #     r = await self.post(
    #         _url=self.api["piston"]["execute"],
    #         _json=True,
    #         data={
    #             "language": language,
    #             "source": code,
    #         },
    #     )
    #     return r

    # /////////////////////////////////////////////////////////////////////////
    # http
    # /////////////////////////////////////////////////////////////////////////

    async def get(self, _url, _json=False, **kwargs):
        async with self.session.get(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    async def post(self, _url, _json=False, **kwargs):
        async with self.session.post(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    async def put(self, _url, _json=False, **kwargs):
        async with self.session.put(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    async def delete(self, _url, _json=False, **kwargs):
        async with self.session.delete(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())
