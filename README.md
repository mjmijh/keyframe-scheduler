# Keyframe Scheduler v3.0.10

Home Assistant Integration für zeitbasierte Keyframe-Interpolation von Licht-Werten (Brightness, Color Temperature).

---

## 📚 How To Use - Mit PICOlightnode

### Schritt 1: Keyframe Scheduler Sensor erstellen

**In Home Assistant:**
1. Settings → Devices & Services → Keyframe Scheduler
2. Configure → Add Sensor
3. Erstelle deinen Zeitplan mit Keyframes

**Beispiel Sensor:**
```yaml
sensor.office_lighting:
  keyframes:
    - time: "06:00"
      brightness: 0.1
      temperature: 2700
    - time: "09:00"
      brightness: 0.8
      temperature: 5000
    - time: "18:00"
      brightness: 0.5
      temperature: 3500
    - time: "22:00"
      brightness: 0.1
      temperature: 2200
```

**Sensor Output:**
```yaml
sensor.office_lighting:
  state: 127  # brightness (0-255)
  attributes:
    brightness_01: 0.5        # 0.0-1.0
    temperature_k: 3500       # Kelvin
    transition_seconds: 2.5   # Empfohlene Transition
```

---

### Schritt 2: Follower Blueprint Automation erstellen

**In Home Assistant:**
1. Settings → Automations & Scenes → Create Automation
2. Wähle Blueprint: **"PICOlightnode: Keyframe Scheduler Follower v4.0"**
3. Konfiguration:

| Parameter | Wert |
|-----------|------|
| **PICOlightnode Light Entity** | `light.pico_101_office_indirekt` |
| **Follow External Switch** | `switch.office_indirekt_externe_automation_zulassen` |
| **Keyframe Scheduler Sensor** | `sensor.office_lighting` |
| **Apply Brightness** | ✅ An |
| **Apply Color Temperature** | ✅ An (falls TC mode) |

---

### Schritt 3: Verwendung

**Starten:**
```
1. Schalte Follow External Switch AN
   → Licht synct smooth zum aktuellen Keyframe (3s transition)
   
2. Keyframe Scheduler läuft automatisch
   → Sendet kontinuierlich Werte an PICO
   → Licht folgt dem Zeitplan
```

**Manuell übernehmen:**
```
1. Ändere Brightness im Dashboard
   → Blueprint detected Manual Override
   → Follow External Switch geht automatisch AUS
   → Du hast jetzt manuelle Kontrolle
```

**Wieder aktivieren:**
```
1. Schalte Follow External Switch wieder AN
   → Licht synct wieder zum aktuellen Keyframe
   → Automation übernimmt
```

---

## 🎯 Wie funktioniert Manual Override Detection?

Der Blueprint erkennt automatisch wenn du das Licht manuell steuerst:

### ✅ **Als Manual Override erkannt:**
- User klickt im Dashboard
- User ändert Brightness/Color Temp
- Service Calls ohne parent_id

**→ Follow External wird automatisch deaktiviert**

### ❌ **NICHT als Manual Override erkannt:**
- Keyframe Blueprint sendet Werte (hat parent_id)
- PICO Integration interne Updates (hat Context ID: `picolightnode_internal`)
- Andere Automations (haben parent_id)

**→ Follow External bleibt aktiv**

---

## 🔧 Blueprint Features

### **A) Smooth Sync on Enable**
Wenn Follow External aktiviert wird, synct das Licht smooth zum aktuellen Keyframe-Wert mit 3 Sekunden Transition.

**Beispiel:**
```
Aktueller Keyframe: brightness=0.8, temp=4000K
Licht ist bei: brightness=0.3, temp=3000K

Follow External AN → Smooth fade zu 0.8 / 4000K über 3s
```

### **B) Context-Aware Detection**
Der Blueprint nutzt Home Assistant Context Tracking um echte User-Aktionen zu erkennen:

```yaml
{% set has_user = trigger.to_state.context.user_id is not none %}
{% set has_parent = trigger.to_state.context.parent_id is not none %}
{% set context_id = trigger.to_state.context.id | default('') %}
{% set from_pico = 'picolightnode' in context_id %}

# Manual Override = User Action, NOT from automation, NOT from PICO internal
{{ has_user and not from_automation and not from_pico }}
```

### **C) Trigger Modes**
- Triggered alle 60 Sekunden UND bei Sensor State Changes
- Garantiert aktuelle Werte auch bei langsamen Transitions

---

## 🌟 Funktioniert mit ALLEN Lights

Der Keyframe Scheduler und Blueprint funktionieren nicht nur mit PICO:

**Unterstützte Light Types:**
- ✅ **PICOlightnode** (via automation override MQTT)
- ✅ Philips Hue
- ✅ WLED
- ✅ Zigbee Lights
- ✅ DMX Fixtures
- ✅ Standard Home Assistant Lights

**Für PICOlightnode:**
- Blueprint sendet Werte via `light.turn_on` service
- PICO Integration übersetzt zu MQTT automation override
- Follow External Switch kontrolliert den Mode

**Für andere Lights:**
- Blueprint sendet direkt via `light.turn_on` service
- Kein Follow External Switch nötig
- Manual Override Detection funktioniert identisch

---

## 📖 Vollständige Dokumentation

Für detaillierte Architektur-Informationen und das Zusammenspiel mit PICOlightnode siehe:

📄 **[PICO_KEYFRAME_CONCEPT.md](https://github.com/mjmijh/picolightnode/blob/main/docs/PICO_KEYFRAME_CONCEPT.md)**

---

## 🎯 Was ist NEU in v3.0.10?

### ✅ PICO Context Detection
- Blueprint erkennt jetzt PICO-interne Updates (Context ID: `picolightnode_internal`)
- Verhindert False-Positive Manual Override Detection
- **Smart Restore wird nicht mehr als Manual Override erkannt**

### ✅ Verbesserte Manual Override Logic
```yaml
# VORHER (v3.0.9):
{{ has_user and not has_parent }}

# JETZT (v3.0.10):
{% set from_pico = 'picolightnode' in context_id %}
{{ has_user and not has_parent and not from_pico }}
```

**Warum?** PICO Smart Restore hat `user_id=None` und `parent_id=None`, würde also als Manual Override erkannt. Mit Context Check wird es jetzt korrekt ignoriert.

---

## 🔧 Installation

### Keyframe Scheduler Integration
```bash
# Via HACS (empfohlen)
1. HACS → Integrations → "+"
2. Suche: "Keyframe Scheduler"
3. Install

# Manuell
cd /config/custom_components
git clone https://github.com/mjmijh/keyframe_scheduler
ha core restart
```

### Blueprint
Wird automatisch mit der Integration installiert:
```
keyframe_scheduler/blueprints/automation/keyframe_smart_light_follower.yaml
```

---

## 💡 Best Practices

### **Tipp 1: Sanfte Transitions**
Nutze ausreichend `transition_seconds` in deinen Keyframes für smooth Übergänge:
```yaml
keyframes:
  - time: "18:00"
    brightness: 0.8
    transition: 5.0  # 5 Sekunden sanfter Übergang
```

### **Tipp 2: Keyframe Density**
Für smooth Helligkeitsverläufe: Mehr Keyframes = smoother
```yaml
# GUT - Smooth Sunrise
06:00 → brightness: 0.0
06:30 → brightness: 0.2
07:00 → brightness: 0.5
08:00 → brightness: 0.8

# WENIGER GUT - Abrupte Sprünge
06:00 → brightness: 0.0
08:00 → brightness: 0.8
```

### **Tipp 3: Follow External bei Bedarf**
Nutze Follow External nur wenn die Automation aktiv sein soll:
```yaml
# Automation um Follow External zeitbasiert zu aktivieren
automation:
  - trigger:
      - platform: time
        at: "06:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.office_indirekt_externe_automation_zulassen
  
  - trigger:
      - platform: time
        at: "23:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.office_indirekt_externe_automation_zulassen
```

---

## 🐛 Troubleshooting

### **Problem: Follow External schaltet sich sofort wieder aus**

**Mögliche Ursachen:**
1. **PICO v2.0.17 oder älter**: Upgrade auf v2.0.18+ (hat Context Tracking)
2. **Blueprint v3.0.9 oder älter**: Upgrade auf v3.0.10+ (hat PICO Context Detection)
3. **Andere Automation**: Checke ob eine andere Automation den Switch controlled

---

### **Problem: Licht reagiert nicht auf Keyframe Änderungen**

**Check:**
1. Ist Follow External Switch **ON**?
2. Läuft die Follower Automation? (Check: Settings → Automations)
3. Hat Automation die richtige Light Entity?
4. Sendet Keyframe Sensor Werte? (Dev Tools → States → sensor.xxx)

---

### **Problem: Manual Override wird nicht erkannt**

**Check:**
1. Ist Follow External Switch aktuell **ON**?
2. Hast du wirklich im Dashboard geklickt? (Service Calls von Scripts zählen als Automation)
3. Logs checken: Blueprint sollte "Manual override detected" loggen

---

## 📦 Requirements

| Component | Minimum Version |
|-----------|----------------|
| Home Assistant | 2024.1.0+ |
| PICOlightnode | v2.0.18+ (für Context Tracking) |

---

## 🔗 Links

- [PICOlightnode Integration](https://github.com/mjmijh/picolightnode)
- [Complete Architecture Documentation](https://github.com/mjmijh/picolightnode/blob/main/docs/PICO_KEYFRAME_CONCEPT.md)
- [Issues & Feature Requests](https://github.com/mjmijh/keyframe_scheduler/issues)
