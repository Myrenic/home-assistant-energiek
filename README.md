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
graph_span: 48h
span:
  start: day
now:
  show: true
  label: Nu
header:
  show: true
  title: Energieprijs per kwartier (€/kwh)
series:
  - entity: sensor.current_electricity_price_all_in
    show:
      legend_value: false
    stroke_width: 2
    float_precision: 3
    type: column
    opacity: 0.3
    color: '#03b2cb'
    data_generator: |
      return entity.attributes.prices.map((record, index) => {
        return [record.from, record.price];
      });
```

## Credits

Special thanks to the authors of the [Frank Energie](https://github.com/bajansen/home-assistant-frank_energie) integration for the inspiration and structure.
