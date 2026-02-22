import asyncio
import argparse
import aiohttp
from urllib.parse import unquote
from datetime import datetime
import json
import logging
import yarl

_LOGGER = logging.getLogger(__name__)


class AuthException(Exception):
    pass


class RequestException(Exception):
    pass


class EnergiekAPI:
    def __init__(self, session: aiohttp.ClientSession = None):
        self.session = session
        self._close_session = False
        self.base_url = "https://mijn.energiek.nl"
        self.org_uuid = None
        self.cluster = None
        self.is_authenticated = False
        self.xsrf_token = None

    async def __aenter__(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._close_session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._close_session and self.session is not None:
            await self.session.close()

    async def _request(self, method, endpoint, **kwargs):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._close_session = True

        headers = self._prepare_headers(kwargs.pop("headers", {}))
        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as response:
                self._update_xsrf_token(url)

                if response.status >= 400:
                    return await self._handle_error(response, url)

                if response.status == 204:
                    return None

                # For endpoints that don't return JSON (if any)
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return await response.json()
                return await response.text()
        except aiohttp.ClientError as err:
            raise RequestException(f"Client error: {err}") from err

    def _prepare_headers(self, custom_headers):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/login"
        }
        headers.update(custom_headers)
        if self.xsrf_token:
            headers["X-XSRF-TOKEN"] = self.xsrf_token
        return headers

    def _update_xsrf_token(self, url):
        yarl_url = yarl.URL(url)
        if 'XSRF-TOKEN' in self.session.cookie_jar.filter_cookies(yarl_url):
            cookie = self.session.cookie_jar.filter_cookies(yarl_url).get('XSRF-TOKEN')
            if cookie:
                self.xsrf_token = unquote(cookie.value)

    async def _handle_error(self, response, url):
        text = await response.text()
        if response.status == 422 and "Geen marktprijs gevonden" in text:
            _LOGGER.debug(f"No market price found for {url}")
            return None
        _LOGGER.error(f"Request failed: {response.status} - {text}")
        if response.status in (401, 403):
            raise AuthException(f"Authentication failed: {response.status}")
        raise RequestException(f"Request failed: {response.status}")

    async def login(self, email, password):
        # 1. Get CSRF + Session
        await self._request("GET", "/api/auth/csrf")
        if not self.xsrf_token:
            raise AuthException("No XSRF token received")

        # 2. Prelogin
        await self._request("POST", "/api/auth/prelogin", json={"username": email})

        # 3. Login
        login_data = await self._request("POST", "/api/auth/login", json={
            "username": email,
            "password": password,
            "remember": None
        })

        if not login_data.get("success"):
            raise AuthException("Login failed")

        org = login_data.get("organizations", [{}])[0]
        self.org_uuid = org.get("uuid")
        clusters = org.get("clusters", [{}])
        if not clusters:
            raise RequestException("No clusters found for user")
        self.cluster = clusters[0].get("cluster")
        self.is_authenticated = True
        return login_data

    async def get_market_prices(self, date_str, market_segment="ELECTRICITY"):
        # date_str format: "YYYY-MM-DD"
        if not self.is_authenticated:
            raise AuthException("Not authenticated. Please login first.")

        params = {
            "frequency": "DAY_QUARTER",
            "date": date_str,
            "marketSegment": market_segment
        }
        headers = {
            "X-Organization": self.org_uuid,
            "X-Cluster": self.cluster
        }

        return await self._request("GET", "/api/dashboard/marketprice", params=params, headers=headers)


async def main():
    parser = argparse.ArgumentParser(description="Energiek API CLI")
    parser.add_argument("--email", required=True, help="Energiek email")
    parser.add_argument("--password", required=True, help="Energiek password")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date to fetch prices for (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--segment",
        default="ELECTRICITY",
        choices=["ELECTRICITY", "GAS"],
        help="Market segment"
    )

    args = parser.parse_args()

    async with EnergiekAPI() as api:
        try:
            await api.login(args.email, args.password)
            print("Login successful!")

            print(f"Fetching {args.segment} prices for {args.date}...")
            prices = await api.get_market_prices(args.date, args.segment)
            print(json.dumps(prices, indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
