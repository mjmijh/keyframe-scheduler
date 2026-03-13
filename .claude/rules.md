# Keyframe Scheduler Development Rules

## Critical Code Patterns

### ✅ Blueprint Context Detection (v4.0+)

**MUST include PICO context check:**

```yaml
# Manual Override Detection - COMPLETE VERSION
- condition: template
  value_template: >
    {% set has_user = trigger.to_state.context.user_id is not none %}
    {% set has_parent = trigger.to_state.context.parent_id is not none %}
    {% set context_id = trigger.to_state.context.id | default('') %}
    {% set from_pico = 'picolightnode' in context_id %}
    
    {# Manual Override = User action, NOT automation, NOT PICO internal #}
    {{ has_user and not has_parent and not from_pico }}
```

**Why each check:**

1. `has_user` - Filters out pure automation triggers (no user involved)
2. `not has_parent` - Filters out automation service calls
3. `not from_pico` - Filters out PICO internal updates (Smart Restore, MQTT)

**❌ OLD VERSION (v3.0.9 and earlier):**
```yaml
# This caused false manual override detection!
{% set has_user = trigger.to_state.context.user_id is not none %}
{% set has_parent = trigger.to_state.context.parent_id is not none %}
{{ has_user and not has_parent }}
# Missing: PICO context check!
```

**Problem with old version:**
- PICO Smart Restore has `user_id=None`, `parent_id=None`
- Would trigger manual override detection ❌
- Follow External would be disabled incorrectly

---

### ✅ Sensor Attribute Naming

**ALWAYS use these exact attribute names:**

```python
self._attr_extra_state_attributes = {
    "brightness_01": float,      # 0.0-1.0 (NOT "brightness" - conflicts!)
    "temperature_k": int,        # Kelvin (NOT "temp" or "color_temp")
    "transition_seconds": float, # Seconds (NOT "transition")
}
```

**Why?**
- `brightness_01` - Avoids confusion with HA's brightness (0-255)
- `temperature_k` - Explicit that it's Kelvin, not mireds
- `transition_seconds` - Explicit unit

**Blueprint reads these:**
```yaml
brightness: >
  {{ state_attr(sensor, 'brightness_01') | float * 255 | int }}
kelvin: >
  {{ state_attr(sensor, 'temperature_k') | int }}
transition: >
  {{ state_attr(sensor, 'transition_seconds') | float }}
```

---

### ✅ Keyframe Time Handling

**Use time strings in 24-hour format:**

```python
# ✅ CORRECT
keyframe = {"time": "18:30", "brightness": 0.5, "temp": 3500}

# ❌ WRONG
keyframe = {"time": "6:30 PM"}  # No AM/PM
keyframe = {"time": 18.5}       # No float hours
keyframe = {"time": "18:30:00"} # No seconds needed
```

**Parse time consistently:**
```python
from datetime import datetime

def parse_time(time_str: str) -> time:
    """Parse HH:MM format."""
    return datetime.strptime(time_str, "%H:%M").time()
```

**Handle midnight rollover:**
```python
def find_next_keyframe(current_time, keyframes):
    """Handle wraparound at midnight."""
    next_kf = None
    min_delta = timedelta.max
    
    for kf in keyframes:
        kf_time = parse_time(kf["time"])
        
        # Calculate delta (may be negative if kf is tomorrow)
        if kf_time >= current_time:
            delta = kf_time - current_time
        else:
            # Tomorrow
            delta = (time(23, 59, 59) - current_time) + (kf_time - time(0, 0, 0))
        
        if delta < min_delta:
            min_delta = delta
            next_kf = kf
    
    return next_kf
```

---

### ✅ Interpolation Accuracy

**Linear interpolation formula:**

```python
def interpolate_value(v1: float, v2: float, ratio: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        v1: Start value
        v2: End value
        ratio: 0.0 to 1.0 (position between v1 and v2)
    
    Returns:
        Interpolated value
    """
    return v1 + (v2 - v1) * ratio
```

**Time ratio calculation:**

```python
def calculate_time_ratio(start_time, end_time, current_time):
    """Calculate ratio (0.0-1.0) of current position."""
    # Convert to seconds since midnight
    def to_seconds(t):
        return t.hour * 3600 + t.minute * 60 + t.second
    
    start_s = to_seconds(start_time)
    end_s = to_seconds(end_time)
    current_s = to_seconds(current_time)
    
    # Handle midnight wraparound
    if end_s < start_s:
        # End time is tomorrow
        if current_s < start_s:
            current_s += 24 * 3600
        end_s += 24 * 3600
    
    total_duration = end_s - start_s
    elapsed = current_s - start_s
    
    return elapsed / total_duration if total_duration > 0 else 0.0
```

**Complete interpolation:**

```python
def get_interpolated_values(keyframes, current_time):
    """Get interpolated brightness and temperature."""
    if not keyframes:
        return 0.5, 3000  # Safe defaults
    
    if len(keyframes) == 1:
        kf = keyframes[0]
        return kf["brightness"], kf["temp"]
    
    # Find surrounding keyframes
    prev_kf, next_kf = find_surrounding_keyframes(keyframes, current_time)
    
    # Calculate ratio
    ratio = calculate_time_ratio(
        parse_time(prev_kf["time"]),
        parse_time(next_kf["time"]),
        current_time
    )
    
    # Interpolate
    brightness = interpolate_value(
        prev_kf["brightness"],
        next_kf["brightness"],
        ratio
    )
    temp = interpolate_value(
        prev_kf["temp"],
        next_kf["temp"],
        ratio
    )
    
    return brightness, temp
```

---

### ✅ Blueprint Smooth Sync

**When Follow External is enabled:**

```yaml
# Sync light to current keyframe value with smooth transition
- service: light.turn_on
  target:
    entity_id: !input target_light
  data:
    brightness: >
      {{ state_attr(scheduler_sensor, 'brightness_01') | float * 255 | int }}
    kelvin: >
      {{ state_attr(scheduler_sensor, 'temperature_k') | int }}
    transition: 3  # 3-second smooth sync
```

**Why 3 seconds?**
- Long enough to be smooth
- Short enough to not be annoying
- User sees light "catch up" to schedule

---

### ✅ Handle Missing/Unavailable States

**Blueprint must handle gracefully:**

```yaml
# Check sensor is available
- condition: template
  value_template: >
    {{ states(scheduler_sensor) not in ['unavailable', 'unknown', 'none'] }}

# Provide defaults for missing attributes
brightness: >
  {% set b = state_attr(scheduler_sensor, 'brightness_01') | default(0.5) %}
  {{ (b * 255) | int }}

kelvin: >
  {% set k = state_attr(scheduler_sensor, 'temperature_k') | default(3000) %}
  {{ k | int }}

transition: >
  {% set t = state_attr(scheduler_sensor, 'transition_seconds') | default(2.0) %}
  {{ t | float }}
```

---

### ✅ Config Flow Validation

**Validate all user inputs:**

```python
import voluptuous as vol

# Brightness validation
vol.Schema({
    vol.Required("brightness"): vol.All(
        vol.Coerce(float),
        vol.Range(min=0.0, max=1.0)
    )
})

# Temperature validation
vol.Schema({
    vol.Required("temperature"): vol.All(
        vol.Coerce(int),
        vol.Range(min=1000, max=10000)
    )
})

# Time validation
vol.Schema({
    vol.Required("time"): vol.All(
        str,
        vol.Match(r'^([01]\d|2[0-3]):([0-5]\d)$')  # HH:MM format
    )
})
```

---

## Error Prevention Checklist

Before committing Blueprint changes:

**Context Detection:**
- [ ] `has_user` check present
- [ ] `has_parent` check present
- [ ] `from_pico` check present (v4.0+)
- [ ] All three combined with AND/NOT logic

**Sensor Attributes:**
- [ ] Using `brightness_01` (not `brightness`)
- [ ] Using `temperature_k` (not `temp`)
- [ ] Using `transition_seconds` (not `transition`)
- [ ] Default values provided for missing attributes

**Interpolation:**
- [ ] Handles midnight rollover
- [ ] Handles single keyframe
- [ ] Handles no keyframes
- [ ] Linear interpolation formula correct

**Blueprint Actions:**
- [ ] Sensor availability check
- [ ] Smooth sync on enable (3s transition)
- [ ] Manual override detection complete
- [ ] Follow External toggle control

---

## Common Bugs

### Bug: Follow External disabled after PICO restore
**Symptom:** Switch goes OFF when light is turned ON
**Cause:** Blueprint v3.0.9 or earlier without PICO context check
**Fix:** Upgrade to Blueprint v4.0 with `from_pico` check

### Bug: Values jump at midnight
**Symptom:** Brightness/temp suddenly changes at 00:00
**Cause:** Midnight rollover not handled in interpolation
**Fix:** Use wraparound logic in time delta calculation

### Bug: Blueprint doesn't apply values
**Symptom:** Light doesn't follow keyframe schedule
**Cause:** Sensor attributes wrong name or missing
**Fix:** Use exact names: `brightness_01`, `temperature_k`, `transition_seconds`

### Bug: Manual override not detected
**Symptom:** User changes brightness but Follow External stays ON
**Cause:** Context detection missing or wrong
**Fix:** Check all three conditions: `has_user and not has_parent and not from_pico`

---

## Blueprint Compatibility Matrix

| Integration | Context ID | Detected as Manual Override? | Notes |
|-------------|-----------|------------------------------|-------|
| User Dashboard | (default) | ✅ YES | Correct - user action |
| User Mobile App | (default) | ✅ YES | Correct - user action |
| **PICOlightnode v2.0.18+** | picolightnode_restore | ❌ NO | Correct - internal restore |
| Adaptive Lighting | (automation ID) | ❌ NO | Correct - automation |
| Other Keyframe Scheduler | (automation ID) | ❌ NO | Correct - automation |
| Node-RED | (automation ID) | ❌ NO | Correct - automation |
| Script Service Call | (depends) | ⚠️ Maybe | Check if script has parent_id |

---

## Performance Rules

### Sensor Updates
```python
# ✅ GOOD - Update every minute
async def async_update(self):
    if datetime.now().second == 0:  # Only on minute boundary
        await self._update_values()

# ❌ BAD - Update every second
async def async_update(self):
    await self._update_values()  # Too frequent!
```

### Blueprint Triggers
```yaml
# ✅ GOOD - Time pattern every minute
- platform: time_pattern
  minutes: "*"

# ❌ BAD - Time pattern every second
- platform: time_pattern
  seconds: "*"  # Too frequent!
```

### Keyframe Lookup
```python
# ✅ GOOD - Binary search O(log n)
keyframes.sort(key=lambda k: k["time"])
index = bisect.bisect_left(keyframes, current_time)

# ❌ BAD - Linear search O(n)
for kf in keyframes:
    if kf["time"] > current_time:
        return kf
```

---

## Documentation Requirements

### Sensor Attributes Must Be Documented
```python
@property
def extra_state_attributes(self):
    """Return sensor attributes.
    
    Attributes:
        brightness_01: float (0.0-1.0) - Current interpolated brightness
        temperature_k: int - Current color temperature in Kelvin
        transition_seconds: float - Recommended transition duration
        current_keyframe: int - Index of current keyframe (debug)
        next_keyframe: int - Index of next keyframe (debug)
    """
    return self._attr_extra_state_attributes
```

### Blueprint Inputs Must Be Clear
```yaml
target_light:
  name: Target Light Entity
  description: >
    The light entity to control. Works with all light types:
    PICOlightnode, Hue, WLED, Zigbee, DMX, etc.
  selector:
    entity:
      domain: light
```

---

## Version Compatibility

### Minimum Requirements
```yaml
# Blueprint v4.0 requires:
- Home Assistant: 2024.1.0+
- PICOlightnode: v2.0.18+ (for context tracking)
- Keyframe Scheduler: v3.0.10+
```

### Backwards Compatibility
```yaml
# Blueprint v4.0 still works with:
- Non-PICO lights (Hue, WLED, etc.)
- Older PICOlightnode versions (but manual override detection may be buggy)
- Other integrations that don't set context
```

**Graceful degradation:**
```yaml
# If context_id doesn't exist, defaults to empty string
{% set context_id = trigger.to_state.context.id | default('') %}
# Empty string doesn't contain "picolightnode" → works as before
```
