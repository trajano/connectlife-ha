"""Provides a switch for ConnectLife."""
import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)
from .coordinator import ConnectLifeCoordinator
from .dictionaries import Dictionaries, Property
from .entity import ConnectLifeEntity
from connectlife.appliance import ConnectLifeAppliance

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ConnectLife sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    for appliance in coordinator.appliances.values():
        dictionary = Dictionaries.get_dictionary(appliance)
        async_add_entities(
            ConnectLifeSwitch(coordinator, appliance, s, dictionary[s])
            for s in appliance.status_list if hasattr(dictionary[s], "switch")
        )


class ConnectLifeSwitch(ConnectLifeEntity, SwitchEntity):
    """Switch class for ConnectLife."""

    def __init__(
            self,
            coordinator: ConnectLifeCoordinator,
            appliance: ConnectLifeAppliance,
            status: str,
            dd_entry: Property
    ):
        """Initialize the entity."""
        super().__init__(coordinator, appliance)
        self._attr_unique_id = f"{appliance.device_id}-{status}"
        self.status = status
        self.entity_description = SwitchEntityDescription(
            key=self._attr_unique_id,
            entity_registry_visible_default=not dd_entry.hide,
            icon=dd_entry.icon,
            name=status.replace("_", " "),
            translation_key=status,
            device_class=dd_entry.switch.device_class
        )
        self.off = dd_entry.switch.off
        self.on = dd_entry.switch.on
        self.update_state()

    @callback
    def update_state(self):
        if self.status in self.coordinator.appliances[self.device_id].status_list:
            value = self.coordinator.appliances[self.device_id].status_list[self.status]
            if value == self.on:
                self._attr_is_on = True
            elif value == self.off:
                self._attr_is_on = False
            else:
                self._attr_is_on = None
                _LOGGER.warning("Unknown value %d for %s", value, self.status)
        self._attr_available = self.coordinator.appliances[self.device_id].offline_state == 1

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        await self.coordinator.api.update_appliance(self.puid, {self.status: str(self.off)})
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        await self.coordinator.api.update_appliance(self.puid, {self.status: str(self.on)})
        self._attr_is_on = True
        self.async_write_ha_state()
