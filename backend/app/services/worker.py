from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.database import session_scope
from app.repositories import (
    claim_next_job,
    get_job,
    mark_job_done,
    mark_job_failed,
    recover_processing_jobs,
    set_job_progress,
)
from app.schemas import ConversionSettings
from app.services.bundler import BatchBundleBuilder
from app.services.docling_adapter import ConversionService
from app.storage import StorageManager

logger = logging.getLogger(__name__)


class WorkerCoordinator:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        storage: StorageManager,
        converter: ConversionService,
        bundler: BatchBundleBuilder,
        max_concurrent_jobs: int = 1,
        poll_interval: float = 1.0,
    ) -> None:
        self.session_factory = session_factory
        self.storage = storage
        self.converter = converter
        self.bundler = bundler
        self.max_concurrent_jobs = max(1, max_concurrent_jobs)
        self.poll_interval = poll_interval
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_concurrent_jobs, thread_name_prefix="docling-worker"
        )
        self.running: dict[Future[None], str] = {}

    def start(self) -> None:
        if self.thread is not None:
            return
        with session_scope(self.session_factory) as session:
            recovered = recover_processing_jobs(session)
            if recovered:
                logger.info("Recovered %s interrupted jobs", recovered)
        self.thread = threading.Thread(
            target=self._run_loop, name="queue-coordinator", daemon=True
        )
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=5)
            self.thread = None
        self.executor.shutdown(wait=True, cancel_futures=False)

    def _run_loop(self) -> None:
        while not self.stop_event.is_set():
            self._reap_finished_futures()
            while len(self.running) < self.max_concurrent_jobs:
                with session_scope(self.session_factory) as session:
                    job_id = claim_next_job(session)
                if job_id is None:
                    break
                future = self.executor.submit(self._process_job, job_id)
                self.running[future] = job_id
            self.stop_event.wait(self.poll_interval)
        self._reap_finished_futures(wait_for_all=True)

    def _reap_finished_futures(self, wait_for_all: bool = False) -> None:
        finished = [future for future in self.running if future.done() or wait_for_all]
        for future in finished:
            job_id = self.running.pop(future)
            try:
                future.result()
            except Exception:
                logger.exception("Worker future crashed for job %s", job_id)

    def _process_job(self, job_id: str) -> None:
        try:
            with session_scope(self.session_factory) as session:
                job = get_job(session, job_id)
                if job is None:
                    return
                source_path = self.storage.resolve(job.stored_pdf_path)
                markdown_path, assets_dir = self.storage.prepare_results_dir(job.id)
                settings = ConversionSettings.model_validate(job.settings_json)

            with session_scope(self.session_factory) as session:
                set_job_progress(session, job_id, 50)

            document = self.converter.convert_document(source_path, settings)

            with session_scope(self.session_factory) as session:
                set_job_progress(session, job_id, 75)

            self.converter.save_markdown(document, markdown_path, assets_dir, settings)

            with session_scope(self.session_factory) as session:
                set_job_progress(session, job_id, 90)
                job = mark_job_done(session, job_id)
                if job is not None:
                    self.bundler.build_for_batch(session, job.batch_id)
        except Exception as exc:
            with session_scope(self.session_factory) as session:
                mark_job_failed(session, job_id, str(exc))
