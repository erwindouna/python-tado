Usage
=====

.. _installation:

Installation
------------

To use Tado Async, first install it using pip:

.. code-block:: console

   (.venv) $ pip install tadoasync

Example setup
----------------

.. code-block:: python

    import asyncio

    from tadoasync import Tado


    async def main() -> None:
        """Show example on how to use aiohttp.ClientSession."""
        async with Tado("username", "password") as tado:
            await tado.get_devices()


    if __name__ == "__main__":
        asyncio.run(main())
