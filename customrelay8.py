"""Custom Relay 8 implementation."""

import logging
import asyncio
import asyncio.tasks
import serialio

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = 3.0
_SEND_READ_TIMEOUT = 0.01


class InvalidResponseException(Exception):
    errno: int
    strerror: str


class CustomRelay8:
    def __init__(self, serial: serialio) -> None:
        self.serial = serial
        self.serial_lock = asyncio.Lock()

    async def __worker(self, cmd: int) -> int:
        try:
            await self.serial.open()
            data = bytearray([cmd])
            _LOGGER.debug("Sending %s", data.hex())
            await self.serial.write(data)
            await asyncio.sleep(_SEND_READ_TIMEOUT)

            recv = await self.serial.read()
            _LOGGER.debug("Received %s", recv.hex())
            return recv
        finally:
            await self.serial.close()

    async def __process(self, cmd: int) -> bytearray:
        await self.serial_lock.acquire()
        try:
            return await asyncio.wait_for(self.__worker(cmd), _TIMEOUT)
        finally:
            self.serial_lock.release()

    async def get_states(self) -> int:
        """Get all states."""
        _LOGGER.info("Get all states")
        states = await self.__process(0)
        if len(states) == 0:
            raise InvalidResponseException("No response received")

        return states[0]

    async def set(self, card: int, relay: int):
        """Set `relay` of `card`."""
        _LOGGER.info("Switch on card %i relay %i", card, relay)
        if not 0 < relay < 9:
            raise Exception("invalid relay number")

        states = await self.__process(relay & 255)
        if len(states) == 0:
            raise InvalidResponseException("No response received")
        if states[0] >> (relay - 1) & 1 != 1:
            raise InvalidResponseException("Wrong response received")

    async def clear(self, card: int, relay: int):
        """Clear `relay` of `card`."""
        _LOGGER.info("Switch off card %i relay %i", card, relay)
        if not 0 < relay < 9:
            raise Exception("invalid relay number")

        states = await self.__process((relay + 10) & 255)
        if len(states) == 0:
            raise InvalidResponseException("No response received")
        if states[0] >> (relay - 1) & 1 != 0:
            raise InvalidResponseException("Wrong response received")
