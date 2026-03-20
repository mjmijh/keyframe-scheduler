# Keyframe Scheduler

Home Assistant Integration für zeitbasierte Keyframe-Interpolation von Licht-Werten (Helligkeit, Farbtemperatur).

Funktioniert mit **allen** HA-Light-Entities — PICOlightnode, Philips Hue, Zigbee, WLED, DMX und Standard-Leuchten.

> Also available in [English](README.md) | También disponible en [Español](README.es.md)

---

## Funktionsweise

Du definierst Keyframes — jeweils mit Uhrzeit, Helligkeit und Farbtemperatur. Die Integration interpoliert stufenlos zwischen ihnen und veröffentlicht die aktuellen Zielwerte als Sensoren. Eine mitgelieferte Blueprint-Automation liest diese Sensoren und wendet die Werte auf deine Leuchten an.

---

## Installation

### Via HACS (empfohlen)

1. HACS → Integrations → `+` → **Keyframe Scheduler** suchen
2. Installieren → Home Assistant neu starten

### Blueprint

Einstellungen → Automationen & Szenen → Blueprints → Blueprint importieren:
```
https://github.com/mjmijh/keyframe-scheduler/blob/main/blueprints/automation/keyframe_smart_light_follower.yaml
```

---

## Setup

### Schritt 1 — Keyframe Scheduler Instanz erstellen

1. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Keyframe Scheduler**
2. Namen vergeben (z.B. `Büro`)
3. Zeitplan per JSON konfigurieren oder die integrierte Webapp verwenden

Die Integration erstellt pro Instanz folgende Sensoren:

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.<name>_target_kelvin` | Aktueller Farbtemperatur-Zielwert in Kelvin |
| `sensor.<name>_target_brightness` | Aktueller Helligkeits-Zielwert (0–100 %) |
| `sensor.<name>_target_mired` | Aktuelle Farbtemperatur in Mired |
| `sensor.<name>_next_change` | Zeitpunkt der nächsten geplanten Wertänderung |

Alle Sensoren haben das Attribut `transition_seconds` — die empfohlene Überblendzeit zum nächsten Keyframe.

### Schritt 2 — Follow Switches einrichten

Ein Follow Switch steuert, ob eine Leuchte dem Zeitplan folgt oder manuell bedient wird.

**PICOlightnode-Leuchten** — jede Leuchte hat bereits einen eigenen Switch:
```
switch.<leuchten_name>_externe_automation_zulassen
```
Direkt im Blueprint auswählen. Kein weiterer Schritt nötig.

**Alle anderen Leuchten** — automatische Follow Switches erstellen:
1. Einstellungen → Geräte & Dienste → Keyframe Scheduler → **Konfigurieren**
2. Unter **Follow Lights**: Leuchten auswählen, die einen Follow Switch erhalten sollen
3. Speichern → Integration lädt neu

Erstellte Switches folgen diesem Muster:
```
switch.keyframe_<instanz>_<leuchte>_follow
```

### Schritt 3 — Blueprint Automation pro Leuchte erstellen

1. Einstellungen → Automationen & Szenen → Automation erstellen → **Aus Blueprint**
2. Wählen: **Keyframe Scheduler**

| Parameter | Beschreibung |
|-----------|-------------|
| **Keyframe Scheduler Sensor** | Beliebiger Sensor der Instanz (z.B. `sensor.buero_target_kelvin`) |
| **Ziel-Leuchte** | Die zu steuernde Light-Entity |
| **Follow Switch** *(optional)* | PICOlightnode-Switch oder auto-generierter Keyframe-Switch |
| **Auto-Resume** *(optional)* | Minuten bis zur automatischen Reaktivierung nach manuellem Override |
| **Sync bei Aktivierung** | Sofort zu aktuellen Zeitplanwerten springen wenn Follow Switch eingeschaltet wird |

Pro Leuchte eine separate Blueprint-Automation erstellen.

---

## Follow Switch Verhalten

```
Follow Switch AN  →  Leuchte folgt dem Keyframe-Zeitplan automatisch
Follow Switch AUS →  Manuelle Steuerung (Zeitplan wird ignoriert)
```

### Automatische Deaktivierung bei manuellem Eingriff

Wenn ein Benutzer die Leuchte direkt über das Dashboard oder die App ändert, erkennt das Blueprint dies und schaltet den Follow Switch automatisch aus.

Erkennung über HA Context:
- `context.user_id` vorhanden → ein echter Benutzer hat die Aktion ausgelöst
- `context.parent_id` leer → keine übergeordnete Automation

Nur wenn beides zutrifft, gilt es als manueller Eingriff.

**Nicht als manueller Eingriff gewertet (Follow bleibt aktiv):**
- Das Keyframe Blueprint selbst (hat `parent_id`)
- PICOlightnode interne Updates
- Andere Automationen (haben `parent_id`)

### Sanfte Synchronisation bei Reaktivierung

Wenn der Follow Switch wieder eingeschaltet wird, blendet die Leuchte innerhalb von 3 Sekunden zu den aktuellen Keyframe-Werten über — kein harter Sprung.

### Auto-Resume

Optional eine Auto-Resume-Dauer konfigurieren. Das Blueprint nutzt den `last_changed`-Zeitstempel des Follow Switches selbst — kein Helper Entity nötig.

```
Manueller Eingriff um 14:30 → Follow Switch geht AUS
Auto-Resume = 60 Minuten
→ Um 15:30 geht Follow Switch automatisch wieder AN
```

---

## Mehrere Leuchten pro Instanz

Eine Instanz = ein gemeinsamer Zeitplan. Jede Leuchte bekommt eine eigene Blueprint-Automation und einen eigenen Follow Switch, unabhängig steuerbar:

```
Instanz "Büro" (gemeinsamer Zeitplan)
    ├── light.buero_decke  →  switch.keyframe_buero_buero_decke_follow
    ├── light.buero_schreibtisch  →  switch.keyframe_buero_buero_schreibtisch_follow
    └── light.buero_wand   →  switch.keyframe_buero_buero_wand_follow
```

---

## Webapp

Nach der Installation erscheint **Keyframe Scheduler** als Sidebar-Eintrag in Home Assistant. Die Webapp ermöglicht es, Zeitpläne visuell zu gestalten und als JSON, PDF oder CSV zu exportieren.

Direkte URL: `http://<dein-ha-host>/keyframe_scheduler/index.html`

Verfügbare Sprachen: DE / EN / ES

---

## Voraussetzungen

| Komponente | Mindestversion |
|------------|---------------|
| Home Assistant | 2024.1.0 |
| PICOlightnode *(optional)* | 2.0.18 |

---

## Links

- [Fehler & Feature-Anfragen](https://github.com/mjmijh/keyframe-scheduler/issues)
- [PICOlightnode Integration](https://github.com/mjmijh/picolightnode-ha)
- [CCT Astronomy Integration](https://github.com/mjmijh/cct-astronomy)
