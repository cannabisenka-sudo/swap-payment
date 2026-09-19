import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.telegram.org") as response:
            print("Статус:", response.status)

asyncio.run(test())