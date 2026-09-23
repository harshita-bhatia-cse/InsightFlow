from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ExportService:
    @staticmethod
    def export_summary(dataset_id: int, payload: dict[str, Any]) -> str:
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        file_path = export_dir / f"dataset_{dataset_id}_summary.json"
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(file_path)
