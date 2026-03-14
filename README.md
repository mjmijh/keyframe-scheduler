# Keyframe Scheduler

Home Assistant Integration für zeitbasierte Keyframe-Interpolation von Licht-Werten (Brightness, Color Temperature).

Funktioniert mit **allen** HA-Light-Entities — reguläre Lights, PICOlightnode, Hue, Zigbee, WLED, DMX und mehr.

---

## Installation

### Via HACS (empfohlen)

1. HACS → Integrations → `+`
2. Suche: **Keyframe Scheduler**
3. Install → HA neu starten

### Blueprint

1. Settings → Automations & Scenes → Blueprints → Import Blueprint
2. URL: `https://github.com/mjmijh/keyframe-scheduler/blob/main/blueprints/automation/keyframe_smart_light_follower.yaml`

---

## Setup

### Schritt 1: Keyframe Scheduler Instanz erstellen

1. Settings → Devices & Services → **Add Integration** → Keyframe Scheduler
2. Name vergeben (z.B. `Besprechung`)
3. Configure → Schedule JSON einfügen oder über die Webapp erstellen

Die Integration erstellt automatisch folgende Sensoren:

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.besprechung_target_kelvin` | Aktueller Farbtemperatur-Zielwert |
| `sensor.besprechung_target_brightness` | Aktueller Helligkeits-Zielwert (0–100 %) |
| `sensor.besprechung_target_mired` | Farbtemperatur in Mired |
| `sensor.besprechung_next_change` | Zeitpunkt der nächsten Wertänderung |

Alle Sensoren haben das Attribut `transition_seconds` — die empfohlene Übergangszeit bis zum nächsten Keyframe.

---

### Schritt 2: Follow Switch einrichten

Der Follow Switch steuert, ob eine Lampe dem Zeitplan folgt oder manuell übernommen wurde.

#### Option A — PICOlightnode

PICOlightnode liefert pro Lampe einen eigenen Switch mit:
```
switch.<light_name>_externe_automation_zulassen
```
Dieser wird direkt im Blueprint ausgewählt. **Kein weiterer Schritt nötig.**

#### Option B — Alle anderen Lights

Der Keyframe Scheduler erstellt automatisch Follow Switches pro Lampe:

1. Settings → Devices & Services → Keyframe Scheduler → **Configure**
2. Unter **Follow Lights**: Lampen auswählen, die einen Follow Switch bekommen sollen
3. Speichern → Integration lädt neu

Erstellt werden Switches nach dem Muster:
```
switch.keyframe_besprechung_besprechungsraum_1_follow
switch.keyframe_besprechung_besprechungsraum_2_follow
```

> Eine Keyframe-Instanz kann beliebig viele Lampen haben — jede bekommt einen eigenen Switch und kann damit unabhängig aktiviert/deaktiviert werden.

---

### Schritt 3: Blueprint Automation erstellen

1. Settings → Automations & Scenes → Create Automation → **From Blueprint**
2. Wähle: **Keyframe Scheduler**

| Parameter | Beschreibung |
|-----------|-------------|
| **Keyframe Scheduler Sensor** | Beliebiger Sensor der Instanz (z.B. `sensor.besprechung_target_kelvin`) |
| **Target Light** | Die Lampe, die folgen soll |
| **Follow Switch** *(optional)* | PICOlightnode-Switch oder auto-generierter Keyframe-Switch |
| **Auto-Resume** *(optional)* | Minuten bis automatische Wiederaktivierung nach manuellem Override |
| **Sync on Enable** | Sofort zu aktuellen Kurven-Werten springen wenn Follow Switch AN |

Pro Lampe wird **eine separate Blueprint-Automation** angelegt.

---

## Wie Follow Switches funktionieren

```
Follow Switch ON  →  Lampe folgt dem Keyframe-Zeitplan automatisch
Follow Switch OFF →  Manuelle Kontrolle (Zeitplan wird ignoriert)
```

### Automatische Deaktivierung bei manuellem Override

Sobald ein Nutzer die Lampe manuell über Dashboard oder App ändert, erkennt das Blueprint dies und schaltet den Follow Switch automatisch aus.

Erkennungslogik (HA Context):
- `context.user_id` vorhanden → echter Nutzer hat die Aktion ausgelöst
- `context.parent_id` leer → keine übergeordnete Automation

Nur wenn beides zutrifft, gilt es als manueller Override.

**Nicht als Override erkannt (Follow bleibt aktiv):**
- Keyframe Blueprint selbst (hat `parent_id`)
- PICOlightnode interne Updates
- Andere Automationen (haben `parent_id`)

### Smooth Sync bei Reaktivierung

Wenn der Follow Switch wieder eingeschaltet wird, springt die Lampe mit einer 3s-Transition zu den aktuellen Keyframe-Werten. Kein harter Sprung.

### Auto-Resume

Statt den Follow Switch manuell wieder einzuschalten, kann Auto-Resume konfiguriert werden. Das Blueprint nutzt den `last_changed`-Timestamp des Follow Switches selbst — **kein Helper Entity nötig**.

```
Manueller Override um 14:30 → Follow Switch geht AUS
Auto-Resume = 60 Minuten
→ Um 15:30 geht Follow Switch automatisch wieder AN
```

---

## Mehrere Lampen an einer Instanz

Eine Keyframe-Instanz kann als gemeinsamer Zeitplan für mehrere Räume dienen. Jede Lampe bekommt eine eigene Blueprint-Automation und einen eigenen Follow Switch:

```
Instanz "Besprechung" (gemeinsamer Zeitplan)
    ├── light.besprechungsraum_1  →  switch.keyframe_besprechung_besprechungsraum_1_follow
    ├── light.besprechungsraum_2  →  switch.keyframe_besprechung_besprechungsraum_2_follow
    └── light.besprechungsraum_3  →  switch.keyframe_besprechung_besprechungsraum_3_follow
```

Räume können unabhängig voneinander an/ausgeschaltet oder manuell übernommen werden, ohne andere zu beeinflussen.

---

## Troubleshooting

### Follow Switch schaltet sich sofort wieder aus

- Prüfen ob eine andere Automation den Switch steuert
- Logs checken: Settings → System → Logs → nach `keyframe_scheduler` filtern

### Licht reagiert nicht auf Keyframe-Änderungen

1. Ist der Follow Switch **AN**?
2. Läuft die Blueprint-Automation? (Settings → Automations)
3. Sendet der Sensor Werte? (Developer Tools → States → `sensor.xxx_target_kelvin`)

### Manueller Override wird nicht erkannt

- Wurde die Änderung wirklich im Dashboard/App vorgenommen? (Automations und Scripts zählen nicht)
- Bei PICOlightnode v2.0.17 oder älter: Upgrade auf v2.0.18+ für Context Tracking

---

## Requirements

| Component | Version |
|-----------|---------|
| Home Assistant | 2024.1.0+ |
| PICOlightnode *(optional)* | v2.0.18+ |

---

## Links

- [PICOlightnode Integration](https://github.com/mjmijh/picolightnode)
- [Issues & Feature Requests](https://github.com/mjmijh/keyframe-scheduler/issues)
