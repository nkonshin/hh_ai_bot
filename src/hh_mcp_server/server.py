from fastmcp import FastMCP

from .hh_client import HHClient

mcp = FastMCP("hh-job-search")

_client: HHClient | None = None


def _get_client() -> HHClient:
    global _client
    if _client is None:
        _client = HHClient()
    return _client


@mcp.tool
async def search_vacancies(
    text: str,
    area: str | None = None,
    salary_from: int | None = None,
    experience: str | None = None,
    employment: str | None = None,
    schedule: str | None = None,
    per_page: int = 20,
) -> dict:
    """Search for vacancies on hh.ru.

    Args:
        text: Search query (e.g. "Python backend developer")
        area: Region ID (1=Moscow, 2=Saint Petersburg). See hh.ru API docs for full list.
        salary_from: Minimum salary filter
        experience: Required experience: noExperience, between1And3, between3And6, moreThan6
        employment: Employment type: full, part, project, volunteer, probation
        schedule: Work schedule: fullDay, shift, flexible, remote, flyInFlyOut
        per_page: Results per page (max 100, default 20)
    """
    params: dict = {"text": text, "per_page": min(per_page, 100)}
    if area:
        params["area"] = area
    if salary_from is not None:
        params["salary"] = salary_from
        params["only_with_salary"] = "true"
    if experience:
        params["experience"] = experience
    if employment:
        params["employment"] = employment
    if schedule:
        params["schedule"] = schedule

    data = await _get_client().search_vacancies(params)

    vacancies = []
    for v in data.get("items", []):
        salary = v.get("salary")
        salary_str = None
        if salary:
            parts = []
            if salary.get("from"):
                parts.append(f"from {salary['from']}")
            if salary.get("to"):
                parts.append(f"to {salary['to']}")
            currency = salary.get("currency", "")
            salary_str = " ".join(parts) + f" {currency}"

        vacancies.append({
            "id": v["id"],
            "name": v["name"],
            "employer": v.get("employer", {}).get("name"),
            "salary": salary_str,
            "area": v.get("area", {}).get("name"),
            "url": v.get("alternate_url"),
            "published_at": v.get("published_at"),
        })

    return {
        "found": data.get("found", 0),
        "pages": data.get("pages", 0),
        "per_page": data.get("per_page", 20),
        "vacancies": vacancies,
    }


@mcp.tool
async def get_vacancy(vacancy_id: str) -> dict:
    """Get detailed information about a specific vacancy.

    Args:
        vacancy_id: Vacancy ID from hh.ru
    """
    v = await _get_client().get_vacancy(vacancy_id)

    salary = v.get("salary")
    salary_str = None
    if salary:
        parts = []
        if salary.get("from"):
            parts.append(f"from {salary['from']}")
        if salary.get("to"):
            parts.append(f"to {salary['to']}")
        currency = salary.get("currency", "")
        salary_str = " ".join(parts) + f" {currency}"

    return {
        "id": v["id"],
        "name": v["name"],
        "employer": v.get("employer", {}).get("name"),
        "salary": salary_str,
        "area": v.get("area", {}).get("name"),
        "description": v.get("description"),
        "key_skills": [s["name"] for s in v.get("key_skills", [])],
        "experience": v.get("experience", {}).get("name"),
        "employment": v.get("employment", {}).get("name"),
        "schedule": v.get("schedule", {}).get("name"),
        "url": v.get("alternate_url"),
        "apply_alternate_url": v.get("apply_alternate_url"),
        "type": v.get("type", {}).get("id"),
        "has_test": v.get("has_test", False),
        "response_letter_required": v.get("response_letter_required", False),
        "published_at": v.get("published_at"),
    }


@mcp.tool
async def get_my_resumes() -> dict:
    """Get list of current user's resumes on hh.ru."""
    data = await _get_client().get_resumes()

    resumes = []
    for r in data.get("items", []):
        resumes.append({
            "id": r["id"],
            "title": r.get("title"),
            "status": r.get("status", {}).get("name"),
            "url": r.get("alternate_url"),
            "updated_at": r.get("updated_at"),
        })

    return {"resumes": resumes}


@mcp.tool
async def get_similar_vacancies(resume_id: str, per_page: int = 20) -> dict:
    """Get vacancies similar to a specific resume.

    Args:
        resume_id: Resume ID from hh.ru
        per_page: Results per page (max 100, default 20)
    """
    data = await _get_client().get_similar_vacancies(
        resume_id, {"per_page": min(per_page, 100)}
    )

    vacancies = []
    for v in data.get("items", []):
        salary = v.get("salary")
        salary_str = None
        if salary:
            parts = []
            if salary.get("from"):
                parts.append(f"from {salary['from']}")
            if salary.get("to"):
                parts.append(f"to {salary['to']}")
            currency = salary.get("currency", "")
            salary_str = " ".join(parts) + f" {currency}"

        vacancies.append({
            "id": v["id"],
            "name": v["name"],
            "employer": v.get("employer", {}).get("name"),
            "salary": salary_str,
            "area": v.get("area", {}).get("name"),
            "url": v.get("alternate_url"),
        })

    return {
        "found": data.get("found", 0),
        "vacancies": vacancies,
    }


@mcp.tool
async def apply_to_vacancy(vacancy_id: str, resume_id: str, message: str) -> dict:
    """Apply to a vacancy on hh.ru with a cover letter.

    Checks if the vacancy accepts API applications before applying.

    Args:
        vacancy_id: Vacancy ID to apply to
        resume_id: Resume ID to use for the application
        message: Cover letter text
    """
    # Pre-check: fetch vacancy to verify it can be applied to via API
    v = await _get_client().get_vacancy(vacancy_id)

    vacancy_type = v.get("type", {}).get("id")
    if vacancy_type == "direct":
        return {
            "success": False,
            "error": "This vacancy has an external application URL. Apply directly on the employer's website.",
            "apply_url": v.get("apply_alternate_url"),
        }

    if v.get("has_test"):
        return {
            "success": False,
            "error": "This vacancy requires a test that must be completed on hh.ru website.",
        }

    await _get_client().apply(vacancy_id, resume_id, message)

    return {
        "success": True,
        "vacancy_id": vacancy_id,
        "resume_id": resume_id,
        "message": "Application sent successfully.",
    }


@mcp.tool
async def get_negotiations() -> dict:
    """Get list of current job applications (negotiations) and their statuses."""
    data = await _get_client().get_negotiations()

    negotiations = []
    for n in data.get("items", []):
        vacancy = n.get("vacancy", {})
        negotiations.append({
            "id": n.get("id"),
            "state": n.get("state", {}).get("name"),
            "vacancy_name": vacancy.get("name"),
            "employer": vacancy.get("employer", {}).get("name"),
            "created_at": n.get("created_at"),
            "updated_at": n.get("updated_at"),
            "url": n.get("url"),
        })

    return {"negotiations": negotiations}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
