"""Asynchronous Python client for the Tado API. This is an example file."""

import asyncio
import logging

from tadoasync import Tado

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    """Show example on how to use aiohttp.ClientSession."""
    async with Tado(debug=True) as tado:
        print("Device activation status: ", tado.device_activation_status)  # noqa: T201
        print("Device verification URL: ", tado.device_verification_url)  # noqa: T201

        print("Starting device activation")  # noqa: T201
        await tado.device_activation()

        print("Device activation status: ", tado.device_activation_status)  # noqa: T201

        devices = await tado.get_devices()

        print("Devices: ", devices)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
