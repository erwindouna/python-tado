"""Asynchronous Python client for the Tado API. This is an example file."""

import asyncio

from tado import Tado


async def main() -> None:
    """Show example on how to use aiohttp.ClientSession."""
    async with Tado("username", "password") as tado:
        await tado.get_devices()


if __name__ == "__main__":
    asyncio.run(main())
