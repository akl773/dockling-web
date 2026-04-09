from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.orm import Session

from app.repositories import get_batch, list_batches
from app.storage import StorageManager


class BatchBundleBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def build_for_batch(self, session: Session, batch_id: str) -> Path | None:
        batch = get_batch(session, batch_id)
        if batch is None:
            return None

        bundle_path = self.storage.bundle_path(batch_id)
        completed_jobs = [job for job in batch.jobs if job.status == "done"]
        if not completed_jobs:
            if bundle_path.exists():
                bundle_path.unlink()
            return None

        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
            for job in completed_jobs:
                markdown_path = self.storage.resolve(job.markdown_path)
                assets_dir = self.storage.resolve(job.assets_dir_path)
                if markdown_path.exists():
                    archive.write(
                        markdown_path, arcname=f"{job.zip_entry_name}/output.md"
                    )
                if assets_dir.exists():
                    for path in assets_dir.rglob("*"):
                        if not path.is_file():
                            continue
                        relative_asset = path.relative_to(assets_dir).as_posix()
                        archive.write(
                            path,
                            arcname=f"{job.zip_entry_name}/assets/{relative_asset}",
                        )
        return bundle_path

    def build_for_all_batches(self, session: Session) -> Path | None:
        batches = list_batches(session)
        completed_jobs = [
            job for batch in batches for job in batch.jobs if job.status == "done"
        ]
        if not completed_jobs:
            return None

        bundle_path = self.storage.bundles_dir / "all-batches.zip"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
            for job in completed_jobs:
                prefix = f"batch-{job.batch_id[:8]}/{job.zip_entry_name}"
                markdown_path = self.storage.resolve(job.markdown_path)
                assets_dir = self.storage.resolve(job.assets_dir_path)
                if markdown_path.exists():
                    archive.write(markdown_path, arcname=f"{prefix}/output.md")
                if assets_dir.exists():
                    for path in assets_dir.rglob("*"):
                        if not path.is_file():
                            continue
                        relative_asset = path.relative_to(assets_dir).as_posix()
                        archive.write(
                            path, arcname=f"{prefix}/assets/{relative_asset}"
                        )
        return bundle_path
