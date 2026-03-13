# Keyframe Scheduler Architecture

## Component Overview

```
Keyframe Scheduler Integration
├── Sensor Entity
│   ├── Interpolates values based on time
│   └── Provides attributes (brightness_01, temperature_k, transition_seconds)
│
├── Config Flow
│   └── UI for keyframe configuration
│
├── Store (scheduler.py)
│   ├── Keyframe data persistence
│   └── Interpolation logic
│
└── Blueprint (v4.0)
    ├── Reads sensor attributes
    ├── Applies to light entities
    └── Context-aware manual override detection
```

---

## Data Flow

```
User configures keyframes via UI
    ↓
Store saves keyframes
    ↓
Sensor updates every minute (or on state change)
    ↓
Interpolation calculates current values
    ↓
Sensor attributes updated:
  - brightness_01 (0.0-1.0)
  - temperature_k (Kelvin)
  - transition_seconds
    ↓
Blueprint reads sensor attributes
    ↓
Blueprint calls light.turn_on service
    ↓
Light Entity receives values
    ↓
[For PICO: Light Entity → MQTT → PICO Hardware]
```

---

## Sensor Entity Structure

### State
```python
state = brightness_255  # 0-255 integer
```

### Attributes
```python
attributes = {
    "brightness_01": 0.75,        # 0.0-1.0 float
    "temperature_k": 3500,        # Kelvin integer
    "transition_seconds": 2.5,    # Transition time
    "current_keyframe_index": 3,  # Debug info
    "next_keyframe_time": "18:00" # Debug info
}
```

---

## Keyframe Interpolation

### Linear Interpolation Algorithm
```python
def interpolate(kf1, kf2, current_time):
    """
    kf1: Previous keyframe
    kf2: Next keyframe
    current_time: Current time
    """
    # Calculate time ratio
    total_duration = kf2.time - kf1.time
    elapsed = current_time - kf1.time
    ratio = elapsed / total_duration  # 0.0 to 1.0
    
    # Interpolate brightness
    brightness = kf1.brightness + (kf2.brightness - kf1.brightness) * ratio
    
    # Interpolate temperature
    temp = kf1.temp + (kf2.temp - kf1.temp) * ratio
    
    return brightness, temp
```

### Edge Cases

**Midnight Rollover:**
```python
# Keyframe at 23:00, next at 01:00
# At 00:30, we need to handle day boundary
if next_kf.time < current_kf.time:
    # Wrap around midnight
    total_duration = (24*60 - current_kf.time) + next_kf.time
```

**Single Keyframe:**
```python
# If only one keyframe exists
return keyframe.brightness, keyframe.temp
```

**No Keyframes:**
```python
# Default to safe values
return 0.5, 3000
```

---

## Blueprint v4.0 Architecture

### Purpose
Apply Keyframe Scheduler values to lights with intelligent manual override detection.

### Triggers
```yaml
# 1. Time-based (every minute)
- platform: time_pattern
  minutes: "*"

# 2. Sensor state change
- platform: state
  entity_id: !input scheduler_sensor

# 3. Light state change (for manual override detection)
- platform: state
  entity_id: !input target_light
  attribute: brightness
```

---

### Context-Aware Manual Override Detection

**Goal:** Distinguish between:
- ✅ TRUE user actions (Dashboard clicks) → Disable Follow External
- ❌ Automation updates (Blueprint, PICO restore) → Keep Follow External

**Implementation:**
```yaml
- condition: template
  value_template: >
    {% set has_user = trigger.to_state.context.user_id is not none %}
    {% set has_parent = trigger.to_state.context.parent_id is not none %}
    {% set context_id = trigger.to_state.context.id | default('') %}
    {% set from_pico = 'picolightnode' in context_id %}
    {{ has_user and not has_parent and not from_pico }}
```

**Context Source Detection:**

| Source | user_id | parent_id | context.id | Detected as Manual? |
|--------|---------|-----------|------------|---------------------|
| User Dashboard Click | ✅ | ❌ | (default) | **YES** → Disable Follow |
| User App Change | ✅ | ❌ | (default) | **YES** → Disable Follow |
| Blueprint Action | ❌ | ✅ | (auto) | NO → Keep Follow |
| PICO Smart Restore | ❌ | ❌ | picolightnode_restore | NO → Keep Follow |
| PICO MQTT Update | ❌ | ❌ | picolightnode_internal | NO → Keep Follow |
| Adaptive Lighting | ❌ | ✅ | (auto) | NO → Keep Follow |
| Other Automation | ❌ | ✅ | (auto) | NO → Keep Follow |

**Why This Matters:**

Before v4.0:
```
User turns light ON → PICO Smart Restore → brightness changes
Blueprint sees: user_id=None, parent_id=None → Thinks: "Manual override!"
Blueprint disables Follow External ❌
```

After v4.0:
```
User turns light ON → PICO Smart Restore → brightness changes
Blueprint sees: context.id contains "picolightnode"
Blueprint knows: "This is PICO-internal, not user action"
Blueprint keeps Follow External enabled ✅
```

---

### Blueprint Actions

**1. Apply Keyframe Values**
```yaml
- service: light.turn_on
  target:
    entity_id: !input target_light
  data:
    brightness: >
      {{ state_attr(scheduler_sensor, 'brightness_01') | float * 255 | int }}
    kelvin: >
      {{ state_attr(scheduler_sensor, 'temperature_k') | int }}
    transition: >
      {{ state_attr(scheduler_sensor, 'transition_seconds') | float }}
```

**2. Smooth Sync on Enable**
When Follow External switch is turned ON:
```yaml
- service: light.turn_on
  target:
    entity_id: !input target_light
  data:
    brightness: "{{ current_brightness }}"
    kelvin: "{{ current_kelvin }}"
    transition: 3  # Smooth 3-second sync
```

**3. Manual Override Detection**
When user changes light manually:
```yaml
- service: switch.turn_off  # or input_boolean.turn_off
  target:
    entity_id: !input follow_toggle
```

---

## Integration with PICOlightnode

### How It Works Together

```
┌─────────────────────────────────────────────────────────┐
│ Keyframe Scheduler Integration                         │
│ ├── Sensor: brightness=0.75, temp=3500                 │
│ └── Provides data ONLY (no light control)              │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Keyframe Scheduler Follower Blueprint v4.0             │
│ ├── Reads sensor attributes every minute               │
│ ├── Calls light.turn_on service                        │
│ └── Context-aware manual override detection            │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ PICOlightnode Integration                               │
│ ├── Receives light.turn_on service call                │
│ ├── Translates to MQTT automation_override             │
│ ├── Sets Context(id="picolightnode_restore") on        │
│ │   internal updates                                   │
│ └── Smart Restore saves/restores mode                  │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ PICO Hardware                                           │
│ └── Receives MQTT, controls physical light             │
└─────────────────────────────────────────────────────────┘
```

### Why This Architecture?

**Separation of Concerns:**
- Keyframe Scheduler: Time-based value calculation
- Blueprint: Application logic + manual override detection
- PICOlightnode: MQTT transport + hardware control
- Each component can work independently

**Universal Compatibility:**
- Keyframe Scheduler works with ANY light type
- Not limited to PICO
- Same Blueprint works for Hue, WLED, Zigbee, etc.

**Context Tracking Enables:**
- Blueprint knows when PICO does internal restore
- No false manual override detection
- Seamless user experience

---

## File Structure

```
custom_components/keyframe_scheduler/
├── __init__.py              # Integration setup
├── manifest.json            # Metadata (v3.0.10)
├── config_flow.py           # UI configuration
├── sensor.py                # Sensor entity implementation
├── scheduler.py             # Keyframe interpolation logic
├── store.py                 # Data persistence
├── services.yaml            # Service definitions
├── const.py                 # Constants
├── translations/
│   └── en.json              # UI strings
└── blueprints/
    └── automation/
        └── keyframe_smart_light_follower.yaml  # Blueprint v4.0
```

---

## State Management

### Sensor Updates
```python
# Update sensor every minute
async def async_update(self):
    current_time = datetime.now().time()
    
    # Get current keyframes
    kf1, kf2 = self._find_surrounding_keyframes(current_time)
    
    # Interpolate
    brightness, temp = self._interpolate(kf1, kf2, current_time)
    
    # Update state
    self._attr_native_value = int(brightness * 255)
    self._attr_extra_state_attributes = {
        "brightness_01": brightness,
        "temperature_k": temp,
        "transition_seconds": self._calc_transition(kf1, kf2)
    }
```

### Keyframe Storage
```python
# Stored in .storage/keyframe_scheduler.{entry_id}
{
  "keyframes": [
    {"time": "06:00", "brightness": 0.1, "temp": 2700},
    {"time": "09:00", "brightness": 0.8, "temp": 5000},
    {"time": "18:00", "brightness": 0.5, "temp": 3500},
    {"time": "22:00", "brightness": 0.1, "temp": 2200}
  ]
}
```

---

## Error Handling

### Missing Sensor Attributes
```yaml
# Blueprint handles missing/unavailable gracefully
brightness: >
  {% set b = state_attr(sensor, 'brightness_01') | default(0.5) %}
  {{ (b * 255) | int }}
```

### Unavailable Sensor
```yaml
# Don't send updates if sensor unavailable
- condition: template
  value_template: "{{ states(sensor) not in ['unavailable', 'unknown'] }}"
```

### Invalid Keyframe Data
```python
# Validate in config_flow
if not 0.0 <= brightness <= 1.0:
    raise vol.Invalid("Brightness must be 0.0-1.0")
if not 1000 <= temp <= 10000:
    raise vol.Invalid("Temperature must be 1000-10000K")
```

---

## Performance Considerations

### Update Frequency
- Sensor updates every minute (time_pattern trigger)
- Additional update on keyframe configuration change
- No excessive polling

### Interpolation Efficiency
- O(log n) keyframe lookup (binary search)
- Cached previous keyframe index
- Minimal computation per update

### Blueprint Efficiency
- Debouncing to prevent rapid toggling
- Only sends light.turn_on when values actually change
- Context check is lightweight template operation
