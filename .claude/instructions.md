# Keyframe Scheduler Development Instructions

## Project Type
Home Assistant Custom Integration for time-based keyframe interpolation of light values (brightness, color temperature)

## Current Version
v3.0.10 - PICO Context Detection in Blueprint v4.0

## What This Integration Does
- Interpolates keyframe values over time (brightness, color temp)
- Provides sensor entities with current interpolated values
- Works with ALL light types (Hue, WLED, **PICOlightnode**, Zigbee, DMX, etc.)
- Blueprint applies sensor values to lights with smart manual override detection

## Development Focus
- Universal compatibility (not PICO-specific!)
- Keyframe interpolation accuracy
- Blueprint context-aware manual override detection
- Smooth transitions between keyframes
- Robust sensor state management

## Key Principles

### 1. Integration is Data Provider Only
```python
# The integration DOES:
✅ Interpolate keyframe values based on time
✅ Provide sensor with brightness_01, temperature_k, transition_seconds
✅ Handle keyframe configuration via UI

# The integration DOES NOT:
❌ Send values to lights directly
❌ Know about specific light types
❌ Control MQTT or other protocols
```

### 2. Blueprint Applies Values
- Blueprint reads sensor attributes
- Blueprint sends to lights via `light.turn_on` service
- Blueprint handles manual override detection

### 3. Context-Aware Detection (v4.0+)
Blueprint must distinguish:
- ✅ User actions (disable Follow External)
- ❌ Automation/Integration updates (keep Follow External)

## Code Style
- Type hints everywhere
- Clean sensor attribute updates
- Efficient interpolation algorithms
- Handle edge cases (midnight rollover, missing keyframes)
- Comprehensive logging for debugging

## Testing Requirements
Before any commit:
1. Test keyframe interpolation (verify values at different times)
2. Test midnight rollover (23:59 → 00:01)
3. Test Blueprint manual override detection
4. Verify sensor attributes are correct
5. Test with multiple sensor instances

## Integration with PICOlightnode
When working on PICO-related features:
- PICOlightnode sends Context(id="picolightnode_restore") for internal updates
- Blueprint v4.0 must detect this context and NOT treat as manual override
- See blueprint detection logic in rules.md
