import pytest
import httpx
import respx

from hh_mcp_server.hh_client import HHClient
from hh_mcp_server.config import BASE_URL


@pytest.fixture
def client():
    return HHClient(access_token="test-token")


@respx.mock
@pytest.mark.asyncio
async def test_search_vacancies(client):
    respx.get(f"{BASE_URL}/vacancies").mock(
        return_value=httpx.Response(200, json={
            "items": [{"id": "123", "name": "Python Dev"}],
            "found": 1,
            "pages": 1,
            "per_page": 20,
        })
    )
    result = await client.search_vacancies({"text": "Python"})
    assert result["found"] == 1
    assert result["items"][0]["id"] == "123"


@respx.mock
@pytest.mark.asyncio
async def test_get_vacancy(client):
    respx.get(f"{BASE_URL}/vacancies/123").mock(
        return_value=httpx.Response(200, json={
            "id": "123",
            "name": "Python Dev",
            "description": "A great job",
        })
    )
    result = await client.get_vacancy("123")
    assert result["id"] == "123"
    assert result["name"] == "Python Dev"


@respx.mock
@pytest.mark.asyncio
async def test_get_resumes(client):
    respx.get(f"{BASE_URL}/resumes/mine").mock(
        return_value=httpx.Response(200, json={
            "items": [{"id": "abc", "title": "My Resume"}],
        })
    )
    result = await client.get_resumes()
    assert len(result["items"]) == 1


@respx.mock
@pytest.mark.asyncio
async def test_apply(client):
    respx.post(f"{BASE_URL}/negotiations").mock(
        return_value=httpx.Response(201)
    )
    result = await client.apply("123", "abc", "I want this job")
    assert result == {"status": "ok"}


@respx.mock
@pytest.mark.asyncio
async def test_auth_error(client):
    respx.get(f"{BASE_URL}/resumes/mine").mock(
        return_value=httpx.Response(401, json={"description": "token expired"})
    )
    with pytest.raises(RuntimeError, match="auth failed"):
        await client.get_resumes()


@respx.mock
@pytest.mark.asyncio
async def test_rate_limit(client):
    respx.get(f"{BASE_URL}/vacancies").mock(
        return_value=httpx.Response(429, text="rate limited")
    )
    with pytest.raises(RuntimeError, match="rate limit"):
        await client.search_vacancies({"text": "Python"})


@respx.mock
@pytest.mark.asyncio
async def test_headers_sent(client):
    route = respx.get(f"{BASE_URL}/vacancies/1").mock(
        return_value=httpx.Response(200, json={"id": "1", "name": "Test"})
    )
    await client.get_vacancy("1")

    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer test-token"
    assert "HH-MCP-Server" in request.headers["user-agent"]
