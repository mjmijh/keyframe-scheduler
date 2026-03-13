"""Config flow for Keyframe Scheduler integration v2.1.1."""

from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN
from .scheduler import spec_from_dict

_LOGGER = logging.getLogger(__name__)

# Hardware transition limits (in seconds)
HARDWARE_LIMITS = {
    "dali": 90,          # DALI v1/v2 standard: max 90s
    "dali2_extended": 1620,  # DALI-2 Extended Fade: max 27 minutes
    "casambi": 600,      # Casambi Bluetooth Mesh: max 10 minutes
    "zigbee": 600,       # Zigbee: max 10 minutes
    "hue": 600,          # Philips Hue Bridge: max 10 minutes
    "zwave": 300,        # Z-Wave: max 5 minutes
    "generic": 300,      # Generic/Unknown: safe default 5 minutes
}


class KeyframeSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Keyframe Scheduler."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            title = user_input["name"].strip()
            
            return self.async_create_entry(
                title=title,
                data={},
                options={"max_transition_seconds": 300}
            )

        schema = vol.Schema(
            {
                vol.Required("name", default="Living Room"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> KeyframeSchedulerOptionsFlow:
        """Get the options flow for this handler."""
        return KeyframeSchedulerOptionsFlow(config_entry)


class KeyframeSchedulerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Keyframe Scheduler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry
        self._uploaded_schedule = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Check if JSON was provided
            if user_input.get("schedule_json"):
                schedule_json = user_input["schedule_json"].strip()
                
                try:
                    # Remove BOM if present
                    if schedule_json.startswith('\ufeff'):
                        schedule_json = schedule_json[1:]
                    
                    # Parse JSON
                    schedule_obj = json.loads(schedule_json)
                    
                    # Validate
                    spec_from_dict(schedule_obj)
                    
                    # Store
                    self._uploaded_schedule = schedule_json
                    
                except json.JSONDecodeError as err:
                    _LOGGER.error("JSON decode error at line %s column %s: %s", 
                                  err.lineno, err.colno, err.msg)
                    errors["schedule_json"] = "invalid_json"
                except Exception as err:
                    _LOGGER.error("Invalid schedule: %s", err)
                    errors["schedule_json"] = "invalid_schedule"
            
            # If no errors, save
            if not errors:
                hardware_type = user_input.get("hardware_type", "generic")
                
                # Map hardware
                if hardware_type == "custom":
                    max_transition = user_input.get("custom_max_transition", 300)
                else:
                    max_transition = HARDWARE_LIMITS.get(hardware_type, 300)
                
                options = {
                    "max_transition_seconds": max_transition,
                }
                
                if self._uploaded_schedule:
                    options["schedule_json"] = self._uploaded_schedule
                
                return self.async_create_entry(title="", data=options)

        # Get current values
        current_schedule = self._entry.options.get("schedule_json", "")
        current_max_transition = self._entry.options.get("max_transition_seconds", 300)
        
        # Determine current hardware
        current_hardware = "generic"
        for hw_type, limit in HARDWARE_LIMITS.items():
            if limit == current_max_transition:
                current_hardware = hw_type
                break
        
        if current_max_transition not in HARDWARE_LIMITS.values():
            current_hardware = "custom"

        schema = vol.Schema(
            {
                vol.Optional(
                    "schedule_json",
                    description={"suggested_value": current_schedule},
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
                vol.Required(
                    "hardware_type",
                    default=current_hardware if current_hardware else "dali"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "dali", "label": "⚡ DALI v1 (max 90s) - Optimized"},
                            {"value": "dali2_extended", "label": "DALI-2 Extended (max 27min)"},
                            {"value": "casambi", "label": "Casambi (max 10min)"},
                            {"value": "zigbee", "label": "Zigbee (max 10min)"},
                            {"value": "hue", "label": "Philips Hue (max 10min)"},
                            {"value": "zwave", "label": "Z-Wave (max 5min)"},
                            {"value": "generic", "label": "Generic (max 5min)"},
                            {"value": "custom", "label": "Custom..."},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    "custom_max_transition",
                    description={"suggested_value": current_max_transition if current_hardware == "custom" else 300}
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=3600,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="seconds",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": (
                    "📁 Workflow:\n"
                    "1. In Webapp: '⬇️ Als Datei speichern' klicken\n"
                    "2. Datei mit Texteditor öffnen (Notepad, TextEdit, etc.)\n"
                    "3. Inhalt kopieren (Strg+A, Strg+C)\n"
                    "4. Hier einfügen (Strg+V)\n\n"
                    "⚙️ Hardware Type: Bestimmt max. Transition-Zeit für deine Lampen"
                )
            },
        )
