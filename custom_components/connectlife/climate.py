"""Provides a climate entity for ConnectLife."""

import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRECISION_HALVES, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)
from .coordinator import ConnectLifeCoordinator
from .entity import ConnectLifeEntity
from connectlife.appliance import ConnectLifeAppliance, DeviceType

_LOGGER = logging.getLogger(__name__)

TEMPERATUR_UNIT = [UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT]
FAN_MODES_MAP = {
    0: "auto",
    5: "super low",
    6: "low",
    7: "medium",
    8: "high",
    9: "super high"
}
FAN_MODES = FAN_MODES_MAP.values()
HVAC_MODES = [HVACMode.FAN_ONLY, HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY, HVACMode.AUTO]

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ConnectLife climatye entities."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([
        ConnectLifeClimateEntity(coordinator, a) for a
        in coordinator.appliances.values()
        if a.device_type == DeviceType.HVAC
    ])

class ConnectLifeClimateEntity(ConnectLifeEntity, ClimateEntity):
    """Class for ConnectLife HVAC devices."""

    _attr_name = None
    _attr_precision = PRECISION_HALVES
    _attr_target_temperature_step = 1
    _attr_hvac_modes = HVAC_MODES
    _attr_fan_modes = FAN_MODES

    def __init__(self, coordinator: ConnectLifeCoordinator, appliance: ConnectLifeAppliance):
        """Initialize the entity."""
        super().__init__(coordinator, appliance)
        self._attr_unique_id = {appliance.device_id}
        self._handle_coordinator_update()
        self._attr_max_temp = 32 if self._attr_temperature_unit == UnitOfTemperature.CELSIUS else 90
        self._attr_min_temp = 16 if self._attr_temperature_unit == UnitOfTemperature.CELSIUS else 61
        _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF
        # TODO: Add fan speed and swing mode

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_temperature_unit = TEMPERATUR_UNIT[self.coordinator.appliances[self.device_id].status_list["t_temp_type"]]

        self._attr_target_temperature = self.coordinator.appliances[self.device_id].status_list["t_temp"]
        self._attr_current_temperature = self.coordinator.appliances[self.device_id].status_list["f_temp_in"]
        self._attr_fan_mode = FAN_MODE_MAP[self.coordinator.appliances[self.device_id].status_list["t_fan_speed"]]

        # $this->modeOptions = $this->extractMetadata($deviceConfiguration, 't_work_mode');
        # $this->fanSpeedOptions = $this->extractMetadata($deviceConfiguration, 't_fan_speed');
        # $this->swingOptions = $this->extractSwingModes($deviceConfiguration);
        # $this->fanSpeed = array_search($connectLifeAcDeviceStatus['statusList']['t_fan_speed'], $this->fanSpeedOptions);
        #
        # foreach ($this->swingOptions as $k => $v) {
        #   if (
        #     $v['t_swing_direction'] === ($connectLifeAcDeviceStatus['statusList']['t_swing_direction'] ?? null) &&
        #     $v['t_swing_angle'] === ($connectLifeAcDeviceStatus['statusList']['t_swing_angle'] ?? null)
        #   ) {
        #     $this->swing = $k;
        #   }
        # }
        #
        # $this->mode = $connectLifeAcDeviceStatus['statusList']['t_power'] === '0'
        #   ? 'off'
        #   : array_search($connectLifeAcDeviceStatus['statusList']['t_work_mode'], $this->modeOptions);
        #



