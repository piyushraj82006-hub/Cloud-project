import { DownloadSimple, ArrowSquareOut, FileText } from '@phosphor-icons/react'

interface ReportLinkProps {
  pdfUrl: string | null
  generatingPdf: boolean
  onGeneratePDF: () => void
}

export function ReportLink({ pdfUrl, generatingPdf, onGeneratePDF }: ReportLinkProps) {
  return (
    <>
      <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <FileText size={14} weight="regular" />
        View Full Report
      </button>
      {pdfUrl ? (
        <a
          href={pdfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
        >
          <DownloadSimple size={14} weight="regular" />
          Download PDF
          <ArrowSquareOut size={12} weight="regular" style={{ opacity: 0.5 }} />
        </a>
      ) : (
        <button
          onClick={onGeneratePDF}
          disabled={generatingPdf}
          className="btn btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            opacity: generatingPdf ? 0.6 : 1,
          }}>
          {generatingPdf ? (
            <>
              <div className="spinner" />
              Generating PDF...
            </>
          ) : (
            <>
              <DownloadSimple size={14} weight="regular" />
              Generate PDF Report
            </>
          )}
        </button>
      )}
    </>
  )
}
