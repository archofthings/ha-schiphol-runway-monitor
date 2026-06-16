# Schiphol Runway Monitor

[![HACS Custom][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]
[![License: MIT][license-badge]][license-url]

A Home Assistant custom integration that monitors live runway usage at Amsterdam Airport Schiphol (EHAM). It creates one sensor per runway, a combined peak-time sensor, and two boolean sensors for inbound and outbound peaks — all updated every 5 minutes from LVNL (Luchtverkeersleiding Nederland) data.

---

## Features

- **6 runway sensors** — one per Schiphol runway, each with four states: `not_in_use`, `inbound`, `outbound`, `inbound_and_outbound`
- **Peak time sensors** — combined state sensor plus two boolean sensors (`binary_sensor`) for inbound and outbound peaks individually
- **Rich attributes** — active headings, next peak windows, raw LVNL data
- **Lovelace dashboard card** — SVG map of all runways with live color coding
- **No API key required** — uses publicly available LVNL data via dutchplanespotters.nl
- **Configurable poll interval** — default 5 minutes, adjustable via the UI

---

## Data Source

Data is sourced from **[dutchplanespotters.nl](https://www.dutchplanespotters.nl/runways/ams/)**, which aggregates real-time runway usage data from LVNL (the Dutch air traffic control authority). LVNL publishes runway changes every 5 minutes.

> ⚠️ **Important**: The data reflects *actual current* runway usage. There is no publicly available source for *future* runway assignments — runway selection depends on real-time wind and traffic conditions.

---

## Entities

### Runway Sensors (`sensor.*`)

One sensor is created per runway. Entity IDs follow the pattern `sensor.{designator}_{name}`:

| Entity ID | Runway | Name |
|-----------|--------|------|
| `sensor.06_24_kaagbaan` | 06/24 | Kaagbaan |
| `sensor.09_27_oostbaan` | 09/27 | Oostbaan |
| `sensor.18c_36c_zwanenburgbaan` | 18C/36C | Zwanenburgbaan |
| `sensor.18l_36r_aalsmeerbaan` | 18L/36R | Aalsmeerbaan |
| `sensor.18r_36l_polderbaan` | 18R/36L | Polderbaan |
| `sensor.04_22_buitenveldertbaan` | 04/22 | Buitenveldertbaan |

#### States

| State | Meaning |
|-------|---------|
| `not_in_use` | Runway is not active |
| `inbound` | Runway is being used for landings |
| `outbound` | Runway is being used for takeoffs |
| `inbound_and_outbound` | Runway is used for both simultaneously |

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `runway` | string | Runway designator, e.g. `"18L/36R"` |
| `name` | string | Dutch name, e.g. `"Aalsmeerbaan"` |
| `landing_heading` | string \| null | Active landing heading, e.g. `"18L"`, or `null` if not landing |
| `takeoff_heading` | string \| null | Active takeoff heading, e.g. `"36R"`, or `null` if not departing |
| `all_active_landing` | list | All runway headings currently used for landings at Schiphol |
| `all_active_takeoff` | list | All runway headings currently used for takeoffs at Schiphol |
| `data_source` | string | Attribution: `"LVNL via dutchplanespotters.nl"` |

---

### Peak Time Sensor (`sensor.schiphol_peak_time`)

Reflects the current peak period status. Schiphol operates more runways simultaneously during peaks: 2 landing + 1 takeoff during inbound peaks, and 1 landing + 2 takeoff during outbound peaks.

#### States

| State | Meaning |
|-------|---------|
| `no_peak` | No peak period active |
| `inbound_peak` | Arrival peak active (high landing volume) |
| `outbound_peak` | Departure peak active (high departure volume) |
| `inbound_and_outbound_peak` | Both peaks overlap |

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `inbound_peak` | bool | `true` if inbound peak is currently active |
| `outbound_peak` | bool | `true` if outbound peak is currently active |
| `next_inbound_peak` | string \| null | Next inbound peak window, e.g. `"15:20 - 16:50"`, or `null` |
| `next_outbound_peak` | string \| null | Next outbound peak window, e.g. `"14:00 - 15:40"`, or `null` |
| `all_peaks` | list | Full list of peak windows for the day, e.g. `[{"inbound": "07:10 - 09:50", "outbound": "06:50 - 08:00"}, ...]` |
| `data_source` | string | Attribution |

> ℹ️ Peak windows are derived from LVNL observations over the past 14 days and represent *typical* patterns. Actual peaks may shift slightly.

---

### Inbound Peak Binary Sensor (`binary_sensor.schiphol_inbound_peak`)

Simple boolean: `on` when an inbound (landing) peak is currently active, `off` otherwise.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `next_inbound_peak` | string \| null | Next upcoming inbound peak window |
| `all_inbound_peaks` | list | All inbound peak windows for today |

---

### Outbound Peak Binary Sensor (`binary_sensor.schiphol_outbound_peak`)

Simple boolean: `on` when an outbound (departure) peak is currently active, `off` otherwise.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `next_outbound_peak` | string \| null | Next upcoming outbound peak window |
| `all_outbound_peaks` | list | All outbound peak windows for today |

---

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → click the ⋮ menu → **Custom repositories**
3. Add your repository URL and select **Integration** as the category
4. Search for **Schiphol Runway Monitor** and click **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for **Schiphol** and follow the setup wizard

### Manual Installation

1. Download the [latest release][release-url]
2. Copy the `custom_components/schiphol_runways/` folder into your HA config:
   ```
   /config/custom_components/schiphol_runways/
   ```
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration**
5. Search for **Schiphol Runway Monitor** and complete setup

---

## Configuration

During setup you can configure:

| Option | Default | Description |
|--------|---------|-------------|
| Poll interval | `5` minutes | How often to fetch data from LVNL. Minimum 1, maximum 60. LVNL updates data every 5 minutes. |

To change options after setup: **Settings → Devices & Services → Schiphol Runway Monitor → Configure**

---

## Automation Examples

### Notify when Aalsmeerbaan (18L/36R) starts being used for landings

```yaml
automation:
  - alias: "Schiphol | Aalsmeerbaan inbound started"
    trigger:
      - platform: state
        entity_id: sensor.18l_36r_aalsmeerbaan
        to:
          - "inbound"
          - "inbound_and_outbound"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "✈️ Aalsmeerbaan active for landings"
          message: >
            Runway 18L/36R is now being used for landings
            (heading: {{ state_attr('sensor.18l_36r_aalsmeerbaan', 'landing_heading') }}).
```

### Notify when a runway stops being used

```yaml
automation:
  - alias: "Schiphol | Aalsmeerbaan no longer active"
    trigger:
      - platform: state
        entity_id: sensor.18l_36r_aalsmeerbaan
        to: "not_in_use"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "✅ Aalsmeerbaan no longer active"
          message: "Runway 18L/36R is now out of use."
```

### Notify when an inbound peak starts

```yaml
automation:
  - alias: "Schiphol | Inbound peak started"
    trigger:
      - platform: state
        entity_id: binary_sensor.schiphol_inbound_peak
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🛬 Schiphol inbound peak"
          message: "Arrival peak is now active — expect additional landing runways in use."
```

### Watch multiple runways at once

```yaml
automation:
  - alias: "Schiphol | Watched runway became active"
    trigger:
      - platform: state
        entity_id:
          - sensor.18l_36r_aalsmeerbaan
          - sensor.04_22_buitenveldertbaan
          - sensor.09_27_oostbaan
        from: "not_in_use"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: >
            ✈️ Runway active: {{ state_attr(trigger.entity_id, 'runway') }}
          message: >
            {{ state_attr(trigger.entity_id, 'name') }} is now
            {% if trigger.to_state.state == 'inbound' %}active for LANDINGS
            {% elif trigger.to_state.state == 'outbound' %}active for DEPARTURES
            {% else %}active for both landings and departures{% endif %}.
```

---

## Dashboard Card

A visual runway map card is included. It displays all six Schiphol runways as an SVG map and colors each runway based on its current state.

![Dashboard card preview](https://raw.githubusercontent.com/your-repo/schiphol-runways-ha/main/docs/card-preview.png)

**Color coding:**
- ⬜ **Dark blue** — not in use
- 🟢 **Green** — inbound (landings)
- 🟡 **Yellow** — outbound (departures)
- 🟠 **Amber** — both inbound and outbound

### Installation

1. Copy `lovelace_runway_card.html` to `/config/www/schiphol_runway_card.html`
2. Add to your Lovelace dashboard:

```yaml
type: iframe
url: /local/schiphol_runway_card.html
aspect_ratio: 120%
```

Or with the `html-template-card` custom card:

```yaml
type: custom:html-template-card
ignore_line_breaks: true
content: !include /config/www/schiphol_runway_card.html
```

### Simple text card (no custom card needed)

```yaml
type: entities
title: Schiphol Runway Status
entities:
  - entity: sensor.18l_36r_aalsmeerbaan
    name: "18L/36R Aalsmeerbaan"
  - entity: sensor.04_22_buitenveldertbaan
    name: "04/22 Buitenveldertbaan"
  - entity: sensor.09_27_oostbaan
    name: "09/27 Oostbaan"
  - entity: sensor.06_24_kaagbaan
    name: "06/24 Kaagbaan"
  - entity: sensor.18r_36l_polderbaan
    name: "18R/36L Polderbaan"
  - entity: sensor.18c_36c_zwanenburgbaan
    name: "18C/36C Zwanenburgbaan"
  - type: divider
  - entity: binary_sensor.schiphol_inbound_peak
    name: "Inbound Peak Active"
  - entity: binary_sensor.schiphol_outbound_peak
    name: "Outbound Peak Active"
  - entity: sensor.schiphol_peak_time
    name: "Peak Status"
```

---

## About Schiphol Runways

Schiphol has six runways. Which ones are active depends on wind direction, traffic volume, noise regulations, and maintenance.

| Runway | Name | Notes |
|--------|------|-------|
| 18R/36L | Polderbaan | Preferred primary; routes over least-populated areas |
| 06/24 | Kaagbaan | Preferred secondary; NE-SW diagonal |
| 18C/36C | Zwanenburgbaan | Central N-S runway |
| 18L/36R | Aalsmeerbaan | SW of the airport |
| 04/22 | Buitenveldertbaan | Short runway; SE of airport, used mainly for GA and during peaks |
| 09/27 | Oostbaan | Shortest runway; used selectively |

During quiet periods (nights and off-peak): 1 landing + 1 departure runway.  
During inbound peaks: 2 landing + 1 departure runway.  
During outbound peaks: 1 landing + 2 departure runways.  
When peaks overlap: up to 2 + 2.

---

## Troubleshooting

**All sensors show `not_in_use` or `unavailable`**
- Check HA logs: **Settings → System → Logs** → filter by `schiphol_runways`
- Verify HA can reach `dutchplanespotters.nl` — check your firewall or DNS
- Try opening https://www.dutchplanespotters.nl/api/runways/ams in a browser

**Peak sensors not triggering automations**
- Binary sensors expose `on`/`off` states — use `to: "on"` in automations, not `to: "true"`
- Verify the entities exist: **Developer Tools → States** → search `schiphol`

**Icon not showing in HA integration page**
- Requires Home Assistant 2026.3 or later for inline brand icons
- The icon is located at `custom_components/schiphol_runways/brand/icon.png`

**HACS store listing shows "icon not available"**
- This is a known HACS bug ([#5171](https://github.com/hacs/integration/issues/5171)) — the icon still shows correctly in the HA integrations page

---

## Contributing

Pull requests and issues are welcome. When reporting a bug, please include:
- Home Assistant version
- Integration version
- Relevant log entries (Settings → System → Logs → filter `schiphol_runways`)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Data is sourced from [dutchplanespotters.nl](https://www.dutchplanespotters.nl/) which aggregates data from [LVNL](https://www.lvnl.nl/). This integration is not affiliated with LVNL or Amsterdam Airport Schiphol.

---

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://hacs.xyz
[release-badge]: https://img.shields.io/github/v/release/your-repo/schiphol-runways-ha
[release-url]: https://github.com/your-repo/schiphol-runways-ha/releases
[license-badge]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://github.com/your-repo/schiphol-runways-ha/blob/main/LICENSE
