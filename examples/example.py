"""Asynchronous Python client for the Tado API. This is an example file."""

import asyncio

from tado import Tado


async def main() -> None:
    """Show example on how to use aiohttp.ClientSession."""
    async with Tado("e.douna@gmail.com", "bla") as tado:
        print(await tado.get_devices())
        print("do stuff with tado")


if __name__ == "__main__":
    asyncio.run(main())
