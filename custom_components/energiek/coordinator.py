"""Coordinator implementation for Energiek integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TypedDict, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .energiek_api import EnergiekAPI, RequestException, AuthException

LOGGER = logging.getLogger(__name__)


class PriceData:
    def __init__(self, prices: list[dict]):
        self.prices = prices

    @property
    def current_price(self) -> float | None:
        """Get the price for the current time."""
        now = dt_util.utcnow()
        for p in self.prices:
            if p["from"] <= now < (p["from"] + timedelta(minutes=15)):
                return p["price"]
        return None


class EnergiekData(TypedDict):
    electricity: PriceData | None
    gas: PriceData | None
    tomorrow_available: bool


class EnergiekDataUpdateCoordinator(DataUpdateCoordinator):
    """Get the latest data and update the states."""

    api: EnergiekAPI

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: EnergiekAPI
    ) -> None:
        """Initialize the data object."""
        self.hass = hass
        self.entry = entry
        self.api = api

        super().__init__(
            hass,
            LOGGER,
            name="Energiek coordinator",
            update_interval=timedelta(minutes=30),
        )

    async def _async_update_data(self) -> EnergiekData:
        """Get the latest data from Energiek."""
        LOGGER.debug("Fetching Energiek data")

        await self._ensure_authenticated()

        now = dt_util.now()
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            electricity_today = await self.api.get_market_prices(today_str, "ELECTRICITY")
            gas_today = await self.api.get_market_prices(today_str, "GAS")
        except RequestException as ex:
            raise UpdateFailed(ex) from ex

        tomorrow_data = await self._fetch_tomorrow_data(tomorrow_str)

        electricity_prices = self._parse_prices(today_str, electricity_today)
        electricity_prices.extend(self._parse_prices(tomorrow_str, tomorrow_data["electricity"]))

        gas_prices = self._parse_gas_prices(today_str, gas_today)
        gas_prices.extend(self._parse_gas_prices(tomorrow_str, tomorrow_data["gas"]))

        return {
            "electricity": PriceData(prices=electricity_prices),
            "gas": PriceData(prices=gas_prices),
            "tomorrow_available": tomorrow_data["available"],
        }

    async def _ensure_authenticated(self) -> None:
        """Ensure the API is authenticated."""
        try:
            if not self.api.is_authenticated:
                email = self.entry.data.get("email")
                password = self.entry.data.get("password")
                await self.api.login(email, password)
        except AuthException as ex:
            raise ConfigEntryAuthFailed from ex
        except RequestException as ex:
            raise UpdateFailed(ex) from ex

    async def _fetch_tomorrow_data(self, tomorrow_str: str) -> dict[str, Any]:
        """Fetch prices for tomorrow if available."""
        result = {"electricity": None, "gas": None, "available": False}
        try:
            elec = await self.api.get_market_prices(tomorrow_str, "ELECTRICITY")
            gas = await self.api.get_market_prices(tomorrow_str, "GAS")

            if elec and "withTotalVat" in elec and len(elec["withTotalVat"]["series"]) > 0:
                result.update({"electricity": elec, "gas": gas, "available": True})
        except RequestException as ex:
            LOGGER.debug("Tomorrow's prices not yet available: %s", ex)
        return result

    def _parse_prices(self, date_str: str, data: dict | None) -> list[dict]:
        """Parse the 15-minute price series."""
        prices = []
        if not data or "withTotalVat" not in data or "series" not in data["withTotalVat"]:
            return prices

        series = data["withTotalVat"]["series"]
        labels = data["withTotalVat"]["labels"]

        for idx, price_val in enumerate(series):
            if idx < len(labels):
                time_str = labels[idx]["label"]  # "00:00"
                dt_str = f"{date_str} {time_str}"

                # Create naive datetime
                naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                # Localize and convert to UTC
                local_dt = naive_dt.replace(tzinfo=dt_util.get_default_time_zone())
                utc_dt = dt_util.as_utc(local_dt)

                prices.append({
                    "from": utc_dt,
                    "price": price_val
                })
        return prices

    def _parse_gas_prices(self, date_str: str, data: dict | None) -> list[dict]:
        """Parse gas prices."""
        # Gas prices usually have the same structure.
        # Assuming identical structure for now.
        return self._parse_prices(date_str, data)
