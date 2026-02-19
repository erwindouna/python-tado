# Usage

## Installation

To use Tado Async, first install it using pip:

```bash
pip install tadoasync
```

## Example setup

```python
import asyncio

from tadoasync import Tado


async def main() -> None:
    """Example usage of Tado Async to retrieve all devices."""
    async with Tado("username", "password") as tado:
        await tado.get_devices()


if __name__ == "__main__":
    asyncio.run(main())
```

Keep in mind that if you use `async with`, the `__aenter__` and `__aexit__` methods are called automatically. It's recommended you use session control; if you don't use `async with`, you need to call `tado.close()` to close the session.
