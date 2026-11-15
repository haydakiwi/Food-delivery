import json
import os
from pathlib import Path
from typing import Any, ClassVar


class RepositoryDataError(Exception):
    """Base error for missing or malformed data files."""


class JsonRepository:
    entity_name: ClassVar[str] = "record"
    id_prefix: ClassVar[str] = "rec"
    error_class: ClassVar[type[Exception]] = RepositoryDataError
    required_fields: ClassVar[tuple[str, ...]] = ()
    protected_fields: ClassVar[frozenset[str]] = frozenset({"id"})

    def __init__(self, data_path: Path | str) -> None:
        self.data_path = Path(data_path)

    def get_all(self) -> list[dict[str, Any]]:
        """Return every record in the data file."""
        return self._load()

    def get_by_id(self, record_id: str) -> dict[str, Any] | None:
        """Return the record with this ID, or None if it does not exist."""
        for record in self._load():
            if record["id"] == record_id:
                return record
        return None

    def _insert(self, record_data: dict[str, Any]) -> dict[str, Any]:
        """Add a record with a new stable ID; any caller-sent ID is ignored."""
        records = self._load()
        new_record = {**record_data, "id": self._next_id(records)}
        records.append(new_record)
        self._save(records)
        return new_record

    def _update_record(
        self, record_id: str, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update one record, skipping protected fields. None if not found."""
        records = self._load()
        for record in records:
            if record["id"] == record_id:
                allowed = {
                    key: value
                    for key, value in changes.items()
                    if key not in self.protected_fields
                }
                record.update(allowed)
                self._save(records)
                return record
        return None

    def _next_id(self, records: list[dict[str, Any]]) -> str:
        """Highest existing number + 1, so IDs are never reused."""
        numbers = []
        for record in records:
            prefix, _, number = str(record["id"]).partition("_")
            if prefix == self.id_prefix and number.isdigit():
                numbers.append(int(number))
        return f"{self.id_prefix}_{max(numbers, default=0) + 1:03d}"

    def _save(self, records: list[dict[str, Any]]) -> None:
        """Write to a temp file, then atomically replace the real file."""
        temp_path = self.data_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=4)
        os.replace(temp_path, self.data_path)

    def _load(self) -> list[dict[str, Any]]:
        if not self.data_path.exists():
            raise self.error_class(f"Data file not found: {self.data_path}")
        try:
            with self.data_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise self.error_class(
                f"Invalid JSON in {self.data_path}: {exc.msg}"
            ) from exc
        if not isinstance(data, list):
            raise self.error_class(
                f"{self.entity_name.capitalize()} data must be a JSON list"
            )

        seen_ids: set[str] = set()
        for index, record in enumerate(data):
            if not isinstance(record, dict) or "id" not in record:
                raise self.error_class(
                    f"{self.entity_name.capitalize()} at position {index} "
                    "is missing an 'id'"
                )
            missing = [f for f in self.required_fields if f not in record]
            if missing:
                raise self.error_class(
                    f"{self.entity_name.capitalize()} at position {index} "
                    f"is missing required field(s): {', '.join(missing)}"
                )
            if record["id"] in seen_ids:
                raise self.error_class(
                    f"Duplicate {self.entity_name} ID '{record['id']}' "
                    f"found at position {index}"
                )
            seen_ids.add(record["id"])
        return data