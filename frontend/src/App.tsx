import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { JobDetail } from './components/JobDetail'
import { JobTable } from './components/JobTable'
import { UploadPanel } from './components/UploadPanel'
import {
  createBatch,
  fetchBatches,
  fetchJob,
  fetchMarkdown,
  type Batch,
  type FileOverrideState,
  type Job,
  type ConversionSettings,
} from './lib/api'

function flattenJobs(batches: Batch[]): Job[] {
  return batches.flatMap((batch) => batch.jobs.map((job) => ({ ...job, batch_id: batch.id })))
}

export default function App() {
  const queryClient = useQueryClient()
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string>('')

  const batchesQuery = useQuery({
    queryKey: ['batches'],
    queryFn: fetchBatches,
    refetchInterval: 1500,
  })

  const batches = batchesQuery.data ?? []
  const jobs = useMemo(() => flattenJobs(batches), [batches])
  const selectedJobFromList = jobs.find((job) => job.id === selectedJobId) ?? null

  const selectedJobQuery = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => fetchJob(selectedJobId!),
    enabled: selectedJobId !== null,
    refetchInterval: selectedJobFromList && ['queued', 'processing'].includes(selectedJobFromList.status) ? 1500 : false,
  })

  const selectedJob = selectedJobQuery.data ?? selectedJobFromList
  const selectedBatch = batches.find((batch) => batch.id === selectedJob?.batch_id) ?? null

  const markdownQuery = useQuery({
    queryKey: ['markdown', selectedJob?.id],
    queryFn: () => fetchMarkdown(selectedJob!.id),
    enabled: selectedJob?.status === 'done',
  })

  const uploadMutation = useMutation({
    mutationFn: (payload: {
      files: File[]
      settings: ConversionSettings
      overrides: Record<string, FileOverrideState>
    }) => createBatch(payload),
    onSuccess: async (batch) => {
      setFeedback(`Queued ${batch.file_count} file${batch.file_count === 1 ? '' : 's'} in batch ${batch.id.slice(0, 8)}.`)
      setSelectedJobId(batch.jobs[0]?.id ?? null)
      await queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
    onError: (error) => {
      setFeedback(error instanceof Error ? error.message : 'Upload failed')
    },
  })

  const activeJobs = jobs.filter((job) => job.status === 'queued' || job.status === 'processing')
  const historyJobs = jobs.filter((job) => job.status === 'done' || job.status === 'failed')
  const batchesById = Object.fromEntries(batches.map((batch) => [batch.id, batch]))

  return (
    <main className="app-shell">
      <section className="hero panel">
        <p className="eyebrow">Docling Web</p>
        <h1>Local-first Docling conversions with durable history and batch exports.</h1>
        <p className="hero-copy">
          A single-service FastAPI + React stack that queues PDF conversions, stores Markdown output under a persistent volume,
          and keeps Docling model downloads cached across container restarts.
        </p>
        {feedback ? <p className="notice-banner">{feedback}</p> : null}
      </section>

      <section className="layout-grid">
        <div className="column stack-lg">
          <UploadPanel onSubmit={uploadMutation.mutateAsync} isSubmitting={uploadMutation.isPending} />
          <JobTable
            title="Active Queue"
            description="Queued and processing jobs"
            jobs={activeJobs}
            batchesById={batchesById}
            selectedJobId={selectedJobId}
            onSelectJob={setSelectedJobId}
          />
        </div>

        <div className="column stack-lg">
          <JobTable
            title="History"
            description="Completed and failed jobs"
            jobs={historyJobs}
            batchesById={batchesById}
            selectedJobId={selectedJobId}
            onSelectJob={setSelectedJobId}
          />
        </div>

        <div className="column detail-column">
          <JobDetail
            job={selectedJob ?? null}
            batch={selectedBatch}
            markdown={markdownQuery.data ?? ''}
            isMarkdownLoading={markdownQuery.isLoading}
          />
        </div>
      </section>

      {batchesQuery.isLoading ? <p className="footer-note">Loading queue state...</p> : null}
      {batchesQuery.isError ? <p className="footer-note">{String(batchesQuery.error)}</p> : null}
    </main>
  )
}
