"""Support for Custom Relay 8 switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .customrelay8 import CustomRelay8, InvalidResponseException
from .const import DOMAIN, HUB

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


def create_switch_entity(
    config_entry: ConfigEntry, hub: CustomRelay8, card: int, relay: int, is_on: bool
) -> Custom20Relay:
    """Set up an entity for this domain."""
    _LOGGER.debug(
        "Adding Custom Relay 8 switch card %i relay %i with state %s",
        card,
        relay,
        STATE_ON if is_on else STATE_OFF,
    )
    return Custom20Relay(config_entry.entry_id, hub, card, relay, is_on)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Custom Relay 8 switch entities from a config entry."""

    entities = []

    hub: CustomRelay8 = hass.data[DOMAIN][config_entry.entry_id][HUB]
    states = await hub.get_states()
    for card in range(1, 2):
        for relay in range(1, 9):
            entities.append(
                create_switch_entity(
                    config_entry, hub, card, relay, (states >> (relay - 1)) & 1
                )
            )

    async_add_entities(entities)


class Custom20Relay(SwitchEntity):
    """Representation of a Custom Relay 8 switch for relay ports."""

    def __init__(
        self, entry_id: str, hub: CustomRelay8, card: int, relay: int, is_on: bool
    ) -> None:
        """Initialize the Custom Relay 8 switch."""
        self.entry_id = entry_id
        self.hub = hub
        self.card = card
        self.relay = relay
        self.card_name = f"K{self.card}"
        self._attr_name = f"K{card}R{relay}"
        self._attr_unique_id = f"{card}.{relay}"
        self._is_on = is_on

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.card_name)
            },
            name=self.card_name,
            manufacturer="Custom Relay",
            model="8",
        )

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        try:
            await self.hub.set(self.card, self.relay)
        except ConnectionRefusedError as ex:
            _LOGGER.error(ex.strerror)
        except InvalidResponseException as ex:
            _LOGGER.error(ex.strerror)
        else:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        try:
            await self.hub.clear(self.card, self.relay)
        except ConnectionRefusedError as ex:
            _LOGGER.error(ex.strerror)
        except InvalidResponseException as ex:
            _LOGGER.error(ex.strerror)
        else:
            self._is_on = False
            self.async_write_ha_state()
