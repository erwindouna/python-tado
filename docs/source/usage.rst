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
        """Example usage of Tado Async to retrieve all devices."""
        async with Tado("username", "password") as tado:
            await tado.get_devices()


    if __name__ == "__main__":
        asyncio.run(main())


Keep in mind that if you use `async with`, the `aenter` and `aexit` methods are called automatically. It's recommended you use session control, if you don't use `async with`, you need to call `tado.close()` to close the session.
