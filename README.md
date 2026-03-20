# Keyframe Scheduler

Home Assistant integration for time-based keyframe interpolation of light values (brightness, colour temperature).

Works with **all** HA light entities — PICOlightnode, Philips Hue, Zigbee, WLED, DMX, and standard lights.

> Auch verfügbar auf [Deutsch](README.de.md) | También disponible en [Español](README.es.md)

---

## How It Works

You define a set of keyframes — each with a time, brightness, and colour temperature. The integration interpolates smoothly between them and publishes the current target values as sensors. A companion blueprint automation reads those sensors and applies the values to your lights.

---

## Installation

### Via HACS (recommended)

1. HACS → Integrations → `+` → search **Keyframe Scheduler**
2. Install → restart Home Assistant

### Blueprint

Settings → Automations & Scenes → Blueprints → Import Blueprint:
```
https://github.com/mjmijh/keyframe-scheduler/blob/main/blueprints/automation/keyframe_smart_light_follower.yaml
```

---

## Setup

### Step 1 — Create a Keyframe Scheduler instance

1. Settings → Devices & Services → Add Integration → **Keyframe Scheduler**
2. Give it a name (e.g. `Office`)
3. Configure the schedule via JSON or use the built-in webapp

The integration creates the following sensors per instance:

| Sensor | Description |
|--------|-------------|
| `sensor.<name>_target_kelvin` | Current colour temperature target in Kelvin |
| `sensor.<name>_target_brightness` | Current brightness target (0–100 %) |
| `sensor.<name>_target_mired` | Current colour temperature in mired |
| `sensor.<name>_next_change` | Time of next scheduled value change |

All sensors carry a `transition_seconds` attribute — the recommended fade duration to the next keyframe.

### Step 2 — Set up Follow Switches

A Follow Switch controls whether a light follows the schedule or is under manual control.

**PICOlightnode lights** — each light already has a built-in switch:
```
switch.<light_name>_externe_automation_zulassen
```
Select it directly in the blueprint. No extra step needed.

**All other lights** — auto-generate Follow Switches per light:
1. Settings → Devices & Services → Keyframe Scheduler → **Configure**
2. Under **Follow Lights**: select the lights that should get a Follow Switch
3. Save → integration reloads

Generated switches follow this pattern:
```
switch.keyframe_<instance>_<light>_follow
```

### Step 3 — Create a blueprint automation per light

1. Settings → Automations & Scenes → Create Automation → **From Blueprint**
2. Select: **Keyframe Scheduler**

| Parameter | Description |
|-----------|-------------|
| **Keyframe Scheduler Sensor** | Any sensor of the instance (e.g. `sensor.office_target_kelvin`) |
| **Target Light** | The light entity to control |
| **Follow Switch** *(optional)* | PICOlightnode switch or auto-generated Keyframe switch |
| **Auto-Resume** *(optional)* | Minutes until automatic re-enable after manual override |
| **Sync on Enable** | Immediately jump to current schedule values when Follow Switch turns on |

Create one separate blueprint automation per light.

---

## Follow Switch Behaviour

```
Follow Switch ON  →  Light follows the keyframe schedule automatically
Follow Switch OFF →  Manual control (schedule is ignored)
```

### Automatic disable on manual override

When a user changes the light directly via the dashboard or app, the blueprint detects this and turns the Follow Switch off automatically.

Detection uses HA context:
- `context.user_id` is set → a real user triggered the action
- `context.parent_id` is empty → no parent automation

Only when both conditions are met is it treated as a manual override.

**Not treated as manual override (Follow stays active):**
- The Keyframe blueprint itself (has `parent_id`)
- PICOlightnode internal updates
- Other automations (have `parent_id`)

### Smooth sync on re-enable

When the Follow Switch is turned back on, the light fades to the current keyframe values over 3 seconds — no hard jump.

### Auto-Resume

Optionally configure an Auto-Resume duration. The blueprint uses the `last_changed` timestamp of the Follow Switch itself — no helper entity required.

```
Manual override at 14:30 → Follow Switch turns OFF
Auto-Resume = 60 minutes
→ At 15:30 Follow Switch turns ON automatically
```

---

## Multiple lights per instance

One instance = one shared time schedule. Each light gets its own blueprint automation and Follow Switch, independently controllable:

```
Instance "Office" (shared schedule)
    ├── light.office_ceiling  →  switch.keyframe_office_office_ceiling_follow
    ├── light.office_desk     →  switch.keyframe_office_office_desk_follow
    └── light.office_wall     →  switch.keyframe_office_office_wall_follow
```

---

## Webapp

After installation, **Keyframe Scheduler** appears as a sidebar entry in Home Assistant. The webapp lets you visually design schedules and export them as JSON, PDF, or CSV.

Direct URL: `http://<your-ha-host>/keyframe_scheduler/index.html`

Available languages: DE / EN / ES

---

## Requirements

| Component | Minimum version |
|-----------|----------------|
| Home Assistant | 2024.1.0 |
| PICOlightnode *(optional)* | 2.0.18 |

---

## Links

- [Issues & Feature Requests](https://github.com/mjmijh/keyframe-scheduler/issues)
- [PICOlightnode Integration](https://github.com/mjmijh/picolightnode-ha)
- [CCT Astronomy Integration](https://github.com/mjmijh/cct-astronomy)
