import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "database_error"}

    if "database" in payload:
        assert payload["database"]["status"] in {"connected", "error"}
