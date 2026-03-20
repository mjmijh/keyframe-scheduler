# Keyframe Scheduler

Integración de Home Assistant para la interpolación temporal de valores de luz basada en fotogramas clave (brillo, temperatura de color).

Compatible con **todas** las entidades de luz de HA — PICOlightnode, Philips Hue, Zigbee, WLED, DMX y luces estándar.

> Also available in [English](README.md) | Auch verfügbar auf [Deutsch](README.de.md)

---

## Cómo funciona

Defines un conjunto de fotogramas clave — cada uno con una hora, brillo y temperatura de color. La integración interpola suavemente entre ellos y publica los valores objetivo actuales como sensores. Un blueprint de automatización incluido lee esos sensores y aplica los valores a tus luces.

---

## Instalación

### Via HACS (recomendado)

1. HACS → Integraciones → `+` → buscar **Keyframe Scheduler**
2. Instalar → reiniciar Home Assistant

### Blueprint

Configuración → Automatizaciones y escenas → Blueprints → Importar blueprint:
```
https://github.com/mjmijh/keyframe-scheduler/blob/main/blueprints/automation/keyframe_smart_light_follower.yaml
```

---

## Configuración

### Paso 1 — Crear una instancia de Keyframe Scheduler

1. Configuración → Dispositivos y servicios → Añadir integración → **Keyframe Scheduler**
2. Asignar un nombre (p. ej. `Oficina`)
3. Configurar el horario mediante JSON o usar la webapp integrada

La integración crea los siguientes sensores por instancia:

| Sensor | Descripción |
|--------|-------------|
| `sensor.<nombre>_target_kelvin` | Temperatura de color objetivo actual en Kelvin |
| `sensor.<nombre>_target_brightness` | Brillo objetivo actual (0–100 %) |
| `sensor.<nombre>_target_mired` | Temperatura de color actual en mired |
| `sensor.<nombre>_next_change` | Hora del próximo cambio programado |

Todos los sensores incluyen el atributo `transition_seconds` — la duración de fundido recomendada hasta el siguiente fotograma clave.

### Paso 2 — Configurar los interruptores de seguimiento (Follow Switches)

Un Follow Switch controla si una luz sigue el horario o está bajo control manual.

**Luces PICOlightnode** — cada luz ya tiene su propio interruptor:
```
switch.<nombre_luz>_externe_automation_zulassen
```
Seleccionarlo directamente en el blueprint. No se necesita ningún paso adicional.

**Todas las demás luces** — generar Follow Switches automáticamente:
1. Configuración → Dispositivos y servicios → Keyframe Scheduler → **Configurar**
2. En **Follow Lights**: seleccionar las luces que deben obtener un Follow Switch
3. Guardar → la integración se recarga

Los interruptores generados siguen este patrón:
```
switch.keyframe_<instancia>_<luz>_follow
```

### Paso 3 — Crear una automatización de blueprint por luz

1. Configuración → Automatizaciones y escenas → Crear automatización → **Desde blueprint**
2. Seleccionar: **Keyframe Scheduler**

| Parámetro | Descripción |
|-----------|-------------|
| **Sensor de Keyframe Scheduler** | Cualquier sensor de la instancia (p. ej. `sensor.oficina_target_kelvin`) |
| **Luz objetivo** | La entidad de luz a controlar |
| **Follow Switch** *(opcional)* | Interruptor PICOlightnode o interruptor Keyframe generado automáticamente |
| **Auto-Resume** *(opcional)* | Minutos hasta la reactivación automática tras anulación manual |
| **Sincronizar al activar** | Saltar inmediatamente a los valores actuales del horario al encender el Follow Switch |

Crear una automatización de blueprint separada por cada luz.

---

## Comportamiento del Follow Switch

```
Follow Switch ON  →  La luz sigue el horario de fotogramas clave automáticamente
Follow Switch OFF →  Control manual (el horario se ignora)
```

### Desactivación automática ante anulación manual

Cuando un usuario cambia la luz directamente desde el panel o la app, el blueprint lo detecta y apaga el Follow Switch automáticamente.

La detección usa el contexto de HA:
- `context.user_id` presente → un usuario real desencadenó la acción
- `context.parent_id` vacío → no hay automatización padre

Solo cuando se cumplen ambas condiciones se trata como anulación manual.

**No se trata como anulación manual (Follow permanece activo):**
- El propio blueprint de Keyframe (tiene `parent_id`)
- Actualizaciones internas de PICOlightnode
- Otras automatizaciones (tienen `parent_id`)

### Sincronización suave al reactivar

Cuando el Follow Switch se vuelve a encender, la luz se desvanece hasta los valores actuales del fotograma clave en 3 segundos — sin saltos bruscos.

### Auto-Resume

Opcionalmente, configurar una duración de Auto-Resume. El blueprint usa el timestamp `last_changed` del propio Follow Switch — no se necesita ninguna entidad auxiliar.

```
Anulación manual a las 14:30 → Follow Switch se apaga
Auto-Resume = 60 minutos
→ A las 15:30 el Follow Switch se enciende automáticamente
```

---

## Múltiples luces por instancia

Una instancia = un horario compartido. Cada luz obtiene su propia automatización de blueprint y Follow Switch, controlables de forma independiente:

```
Instancia "Oficina" (horario compartido)
    ├── light.oficina_techo      →  switch.keyframe_oficina_oficina_techo_follow
    ├── light.oficina_escritorio →  switch.keyframe_oficina_oficina_escritorio_follow
    └── light.oficina_pared      →  switch.keyframe_oficina_oficina_pared_follow
```

---

## Webapp

Tras la instalación, **Keyframe Scheduler** aparece como entrada en la barra lateral de Home Assistant. La webapp permite diseñar horarios visualmente y exportarlos como JSON, PDF o CSV.

URL directa: `http://<tu-host-ha>/keyframe_scheduler/index.html`

Idiomas disponibles: DE / EN / ES

---

## Requisitos

| Componente | Versión mínima |
|------------|---------------|
| Home Assistant | 2024.1.0 |
| PICOlightnode *(opcional)* | 2.0.18 |

---

## Enlaces

- [Problemas y solicitudes de funciones](https://github.com/mjmijh/keyframe-scheduler/issues)
- [Integración PICOlightnode](https://github.com/mjmijh/picolightnode-ha)
- [Integración CCT Astronomy](https://github.com/mjmijh/cct-astronomy)
