import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _has_infrastructure():
    import socket
    for host, port in [("localhost", 5432), ("localhost", 6379)]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect((host, port))
            s.close()
        except (socket.timeout, OSError):
            return False
    return True


skip_no_infra = pytest.mark.skipif(not _has_infrastructure(), reason="Requires PostgreSQL and Redis")


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "operational"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
@skip_no_infra
async def test_list_tickers(client):
    resp = await client.get("/api/v1/tickers")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_docs(client):
    resp = await client.get("/docs")
    assert resp.status_code == 200


@pytest.mark.asyncio
@skip_no_infra
async def test_dashboard(client):
    resp = await client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    assert "watchlist" in resp.json()
