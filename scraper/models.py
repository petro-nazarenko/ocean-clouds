"""Shared data models for vacancy results."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import json


@dataclass
class Vacancy:
    title: str
    company: str
    rank: str
    vessel_type: str
    region: str
    salary: str
    duration: str
    joining_date: str
    source: str
    url: str
    description: str
    posted_at: str
    is_urgent: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    def matches(
        self,
        rank: Optional[str] = None,
        vessel: Optional[str] = None,
        region: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_duration: Optional[int] = None,
        source_filter: Optional[str] = None,
        urgent_only: bool = False,
    ) -> bool:
        """Return True if this vacancy matches all provided filters (fuzzy, case-insensitive)."""
        def contains(haystack: str, needle: str) -> bool:
            return needle.lower() in haystack.lower()

        if rank and not contains(self.rank + " " + self.title, rank):
            return False
        if vessel and not contains(self.vessel_type, vessel):
            return False
        if region and not contains(self.region, region):
            return False
        if urgent_only and not self.is_urgent:
            return False
        if source_filter and not contains(self.source, source_filter):
            return False
        if min_salary:
            nums = [int(c) for c in self.salary.replace(",", "").split() if c.isdigit()]
            if nums and max(nums) < min_salary:
                return False
        if max_duration:
            nums = [int(c) for c in self.duration.split() if c.isdigit()]
            if nums and min(nums) > max_duration:
                return False
        return True


def save_cache(vacancies: list[Vacancy], path: str) -> None:
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(vacancies),
        "vacancies": [v.to_dict() for v in vacancies],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_cache(path: str) -> list[Vacancy]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Vacancy(**v) for v in data["vacancies"]]
