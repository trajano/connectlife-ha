"""Provides a selector for ConnectLife."""
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
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
    """Set up ConnectLife selectors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    for appliance in coordinator.appliances.values():
        dictionary = Dictionaries.get_dictionary(appliance)
        async_add_entities(
            ConnectLifeSelect(coordinator, appliance, s, dictionary[s])
            for s in appliance.status_list if hasattr(dictionary[s], Platform.SELECT)
        )


class ConnectLifeSelect(ConnectLifeEntity, SelectEntity):
    """Select class for ConnectLife."""

    _attr_current_option = None

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
        self.options_map = dd_entry.select.options
        self.reverse_options_map = {v: k for k, v in self.options_map.items()}
        self.entity_description = SelectEntityDescription(
            key=self._attr_unique_id,
            entity_registry_visible_default=not dd_entry.hide,
            icon=dd_entry.icon,
            name=status.replace("_", " "),
            translation_key=status,
            options=list(self.options_map.values())
        )
        self.update_state()

    @callback
    def update_state(self):
        if self.status in self.coordinator.appliances[self.device_id].status_list:
            value = self.coordinator.appliances[self.device_id].status_list[self.status]
            if value in self.options_map:
                value = self.options_map[value]
            else:
                _LOGGER.warning("Got unexpected value %d for %s", value, self.status)
                _value = None
            self._attr_current_option = value

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.api.update_appliance(self.puid, {self.status: self.reverse_options_map[option]})
        self._attr_current_option = option
        self.async_write_ha_state()
