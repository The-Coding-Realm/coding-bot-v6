import aiohttp
import json
import re
from discord.ext import tasks


class http(aiohttp.ClientSession):
    def __init__(self):
        self.cache = {"piston": {}}
        self.api = {
            "rock": {
                "random": "https://mrconos.pythonanywhere.com/rock/random",
                "top": "https://mrconos.pythonanywhere.com/rock/top",
            },
            "numbers": {
                "random_trivia": "http://numbersapi.com/random/trivia",
                "random_math": "http://numbersapi.com/random/math",
                "random_date": "http://numbersapi.com/random/date",
                "random_year": "http://numbersapi.com/random/year",
                "date": lambda date: f"http://numbersapi.com/{date}/date",
                "year": lambda year: f"http://numbersapi.com/{year}/year",
                "trivia": lambda num: f"http://numbersapi.com/{num}",
                "math": lambda num: f"http://numbersapi.com/{num}/math",
            },
            "piston": {
                "runtimes": "https://emkc.org/api/v2/piston/runtimes",
                # "execute": "https://emkc.org/api/v2/piston/execute",
                "execute": "https://emkc.org/api/v1/piston/execute",
            },
        }
        print("new session")
        super().__init__()
        self.update_data.start()

    @tasks.loop(minutes=5)
    async def update_data(self):
        print("updating cache")
        self.cache["piston"]["runtimes"] = await self.getRuntimes()

    # 🪨 api
    async def getRandomRock(self):
        return await self.get(_url=self.api["rock"]["random"], _json=True)

    async def getTopRock(self):
        return await self.get(_url=self.api["rock"]["top"], _json=True)

    # numbers api
    async def getRandomNumber(self, type="trivia"):
        return await self.get(_url=self.api["numbers"]["random_" + type])

    async def getNumber(self, num, type="trivia"):
        return await self.get(_url=self.api["numbers"][type](num))

    # piston api
    async def getRuntimes(self):
        return await self.get(_url=self.api["piston"]["runtimes"], _json=True)

    async def executeCode(self, language, code):
        r = await self.post(
            _url=self.api["piston"]["execute"],
            _json=True,
            data={
                "language": language,
                "source": code,
            },
        )
        return r

    # http
    async def get(self, _url, _json=False, **kwargs):
        async with super().get(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    async def post(self, _url, _json=False, **kwargs):
        async with super().post(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    async def put(self, _url, _json=False, **kwargs):
        async with super().put(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    async def delete(self, _url, _json=False, **kwargs):
        async with super().delete(_url, **kwargs) as response:
            return await (response.json() if _json else response.text())

    def update_apis(self):
        with open("./web/APIs.json", "r") as file:
            self.api = json.load(file)
            return self.api
