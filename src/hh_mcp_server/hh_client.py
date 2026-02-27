from typing import Any

import httpx

from .config import BASE_URL, USER_AGENT, get_access_token


class HHClient:
    """HTTP client for hh.ru API."""

    def __init__(self, access_token: str | None = None):
        self._token = access_token or get_access_token()
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {self._token}",
                "User-Agent": USER_AGENT,
            },
            timeout=30.0,
        )

    async def _request(self, method: str, url: str, **kwargs: Any) -> dict:
        response = await self._client.request(method, url, **kwargs)
        if response.status_code == 401:
            raise RuntimeError("hh.ru auth failed: token expired or invalid. Refresh it via hh-applicant-tool.")
        if response.status_code == 403:
            raise RuntimeError(f"hh.ru access denied: {response.text}")
        if response.status_code == 429:
            raise RuntimeError("hh.ru rate limit exceeded. Try again later.")
        response.raise_for_status()
        if response.status_code == 201:
            return {"status": "ok"}
        return response.json()

    async def get_resumes(self) -> dict:
        return await self._request("GET", "/resumes/mine")

    async def search_vacancies(self, params: dict) -> dict:
        return await self._request("GET", "/vacancies", params=params)

    async def get_vacancy(self, vacancy_id: str) -> dict:
        return await self._request("GET", f"/vacancies/{vacancy_id}")

    async def get_similar_vacancies(self, resume_id: str, params: dict | None = None) -> dict:
        return await self._request("GET", f"/resumes/{resume_id}/similar_vacancies", params=params or {})

    async def apply(self, vacancy_id: str, resume_id: str, message: str) -> dict:
        return await self._request(
            "POST",
            "/negotiations",
            data={
                "vacancy_id": vacancy_id,
                "resume_id": resume_id,
                "message": message,
            },
        )

    async def get_negotiations(self) -> dict:
        return await self._request("GET", "/negotiations")

    async def close(self) -> None:
        await self._client.aclose()
