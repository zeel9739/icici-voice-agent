import pytest
from httpx import AsyncClient


VALID_PAYLOAD = {
    "name": "Rajesh Kumar",
    "phone_number": "+919876543210",
    "fund_preference": "equity",
}


@pytest.mark.asyncio
async def test_create_lead(client: AsyncClient):
    resp = await client.post("/api/v1/leads", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Rajesh Kumar"
    assert data["status"] == "pending"
    assert data["phone_number"] == "+919876543210"


@pytest.mark.asyncio
async def test_create_duplicate_lead_returns_409(client: AsyncClient):
    await client.post("/api/v1/leads", json=VALID_PAYLOAD)
    resp = await client.post("/api/v1/leads", json=VALID_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_lead(client: AsyncClient):
    create_resp = await client.post("/api/v1/leads", json=VALID_PAYLOAD)
    lead_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/leads/{lead_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == lead_id


@pytest.mark.asyncio
async def test_get_nonexistent_lead_returns_404(client: AsyncClient):
    resp = await client.get("/api/v1/leads/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_lead_status(client: AsyncClient):
    create_resp = await client.post("/api/v1/leads", json=VALID_PAYLOAD)
    lead_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/leads/{lead_id}",
        json={"status": "interested", "fund_preference": "elss"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "interested"
    assert resp.json()["fund_preference"] == "elss"


@pytest.mark.asyncio
async def test_list_leads(client: AsyncClient):
    resp = await client.get("/api/v1/leads")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_delete_lead(client: AsyncClient):
    create_resp = await client.post("/api/v1/leads", json=VALID_PAYLOAD)
    lead_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/leads/{lead_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/leads/{lead_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_phone_returns_422(client: AsyncClient):
    resp = await client.post(
        "/api/v1/leads",
        json={**VALID_PAYLOAD, "phone_number": "not-a-phone"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
