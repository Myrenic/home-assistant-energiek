# Energiek Home Assistant Integration

Home Assistant integration for tracking energy prices from [Energiek](https://mijn.energiek.nl). This integration is inspired by the Frank Energie integration.

## Features

- **Electricity Prices**: Track current and future energy prices (15-minute intervals).
- **Gas Prices**: Track current and future gas prices.
- **ApexCharts Ready**: Includes `prices` attribute for easy graphing with `apexcharts-card`.
- **Status Indicator**: Binary sensor to show when tomorrow's prices are available.

## Installation

### HACS (Recommended)
1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Go to HACS -> Integrations -> 3 dots (top right) -> Custom repositories.
3. Add `https://github.com/Myrenic/home-assistant-energiek` with category `Integration`.
4. Click "Add" and then "Download".
5. Restart Home Assistant.

### Manual
1. Copy the `custom_components/energiek` directory to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings -> Devices & Services**.
2. Click **Add Integration** and search for **Energiek**.
3. Enter your Energiek email and password.

## Graphing Example

You can use the `custom:apexcharts-card` to display the prices:

```yaml
type: custom:apexcharts-card
span:
  start: day
now:
  show: true
  label: Nu
  color: var(--primary-color)
header:
  show: true
  title: Energieprijs per kwartier
  show_states: true
  colorize_states: true
experimental:
  color_threshold: true
apex_config:
  chart:
    type: line
    height: 250
    toolbar:
      show: false
  stroke:
    width: 0
  plotOptions:
    bar:
      borderRadius: 0
  yaxis:
    forceNiceScale: true
    decimalsInFloat: 2
  xaxis:
    type: datetime
    labels:
      datetimeUTC: false
series:
  - entity: sensor.current_electricity_price_all_in
    extend_to: end
    type: column

```

## Credits

Special thanks to the authors of the [Frank Energie](https://github.com/bajansen/home-assistant-frank_energie) integration for the inspiration and structure.
