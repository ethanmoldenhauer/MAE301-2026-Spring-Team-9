from __future__ import annotations

from typing import Iterable, List


def compare_apartments(apartments: List[dict]) -> str:
    if not apartments:
        return "No apartments saved yet."

    lines = ["Apartment comparison:"]
    for apt in apartments:
        total_move_in = float(apt.get("rent", 0)) + float(apt.get("deposit", 0))
        furnished = "Yes" if apt.get("furnished") else "No"
        utilities = "Yes" if apt.get("utilities_included") else "No"
        lines.append(
            f"- {apt.get('title')} in {apt.get('city')}, {apt.get('country')}: "
            f"rent=${apt.get('rent')}, deposit=${apt.get('deposit')}, total move-in about ${total_move_in}, "
            f"furnished={furnished}, utilities included={utilities}"
        )
        if apt.get("url"):
            lines.append(f"  link: {apt.get('url')}")
        if apt.get("notes"):
            lines.append(f"  notes: {apt.get('notes')}")
    return "\n".join(lines)
