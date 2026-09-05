import base64
import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class RazorpayAPIError(Exception):
    """Raised when Razorpay API returns an error response or network failure."""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class RazorpayClient:
    """Production-grade asynchronous Razorpay API client with retry and error handling.

    Supports test mode and production endpoints across Payments, Settlements,
    Settlement Recon, and Refunds.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID", "rzp_test_buildathon2026")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET", "mock_secret_buildathon")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret and self.key_id != "mock_key")

    @property
    def is_test_mode(self) -> bool:
        return self.key_id.startswith("rzp_test_")

    def _get_auth_header(self) -> dict[str, str]:
        token = base64.b64encode(f"{self.key_id}:{self.key_secret}".encode()).decode("ascii")
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "AdaptiveAI-Finance-Controller/1.0",
        }

    async def _request(self, method: str, endpoint: str, params: Optional[dict] = None, data: Optional[dict] = None) -> dict[str, Any]:
        """Sends an authenticated request with retry for transient failures."""
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_auth_header()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            retries = 2
            backoff = 0.5
            for attempt in range(retries + 1):
                try:
                    response = await client.request(method, url, headers=headers, params=params, json=data)
                    if response.status_code == 200:
                        return response.json()
                    if response.status_code == 429:  # Rate limited
                        logger.warning(f"Razorpay rate limit encountered (429). Attempt {attempt + 1}/{retries + 1}")
                        if attempt < retries:
                            import asyncio
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                    
                    error_data = response.json() if response.content else {}
                    err_msg = error_data.get("error", {}).get("description", response.text)
                    err_code = error_data.get("error", {}).get("code", "UNKNOWN_ERROR")
                    raise RazorpayAPIError(f"Razorpay API Error ({response.status_code}): {err_msg}", response.status_code, err_code)
                except httpx.RequestError as exc:
                    if attempt < retries:
                        import asyncio
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    raise RazorpayAPIError(f"Network error connecting to Razorpay: {str(exc)}") from exc
        return {}

    async def fetch_payments(self, count: int = 50, skip: int = 0, from_timestamp: Optional[int] = None) -> list[dict[str, Any]]:
        """Fetch list of payments from Razorpay."""
        params: dict[str, Any] = {"count": count, "skip": skip}
        if from_timestamp:
            params["from"] = from_timestamp
        data = await self._request("GET", "/payments", params=params)
        return data.get("items", [])

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetch individual payment details."""
        return await self._request("GET", f"/payments/{payment_id}")

    async def fetch_settlements(self, count: int = 50, skip: int = 0) -> list[dict[str, Any]]:
        """Fetch settlement batches."""
        params = {"count": count, "skip": skip}
        data = await self._request("GET", "/settlements", params=params)
        return data.get("items", [])

    async def fetch_settlement_recon(self, year: int, month: int, day: Optional[int] = None) -> list[dict[str, Any]]:
        """Fetch settlement reconciliation details."""
        params: dict[str, Any] = {"year": year, "month": month}
        if day:
            params["day"] = day
        data = await self._request("GET", "/settlements/recon/combined", params=params)
        return data.get("items", [])

    async def fetch_refunds(self, count: int = 50, skip: int = 0) -> list[dict[str, Any]]:
        """Fetch refund records."""
        params = {"count": count, "skip": skip}
        data = await self._request("GET", "/refunds", params=params)
        return data.get("items", [])
