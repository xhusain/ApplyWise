import React, { useState } from 'react'

function ResultsDisplay({ results, onDownload, onNewApplication }) {
  const [expandedSection, setExpandedSection] = useState(null)

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return '#6b7280'
    if (score >= 8.5) return '#10b981' // green
    if (score >= 7) return '#f59e0b' // amber
    return '#ef4444' // red
  }

  const formatScore = (score) => (
    score === null || score === undefined ? 'N/A' : Number(score).toFixed(1).replace('.0', '')
  )

  const scoreWidth = (score) => (
    score === null || score === undefined ? '0%' : `${Math.max(0, Math.min(10, Number(score))) * 10}%`
  )

  const scoreRows = [
    ['Resume Quality', results.component_scores?.resume],
    ['Cover Letter', results.component_scores?.cover_letter],
    ['ATS Compatibility', results.component_scores?.ats_compatibility],
    ['Job Alignment', results.component_scores?.job_alignment]
  ]

  const agentLabels = {
    job_finder: 'Job Finder - ReAct',
    resume_tailor: 'Resume Tailor - Chain-of-Thought',
    cover_letter: 'Cover Letter - Tool Use',
    critic: 'Critic - Reflection'
  }

  const agentEntries = Object.entries(results.agent_outputs || {})

  const formatAgentOutput = (value) => {
    if (value === null || value === undefined) return 'No output returned.'
    if (typeof value === 'string') return value
    return JSON.stringify(value, null, 2)
  }

  return (
    <div className="results-container">
      <div className="results-card">
        <h2>🎉 Your Application Package is Ready!</h2>
        
        <div className="quality-summary">
          <div className="score-display">
            <div className="score-circle" style={{ borderColor: getScoreColor(results.quality_score) }}>
              <span className="score-value">{formatScore(results.quality_score)}</span>
              <span className="score-label">{results.quality_score === null || results.quality_score === undefined ? '' : '/10'}</span>
            </div>
            <div className="score-info">
              <h3>Quality Score</h3>
              <p className={results.ready_for_submission ? 'status-ready' : 'status-needs-work'}>
                {results.ready_for_submission ? '✓ Ready for Submission' : '⚠️ Needs Improvement'}
              </p>
            </div>
          </div>
        </div>

        <div className="job-summary">
          <h3>Position Summary</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="label">Position:</span>
              <span className="value">{String(results.job_title)}</span>
            </div>
            <div className="summary-item">
              <span className="label">Company:</span>
              <span className="value">{String(results.company)}</span>
            </div>
            <div className="summary-item">
              <span className="label">Application ID:</span>
              <span className="value">{String(results.job_id)}</span>
            </div>
          </div>
        </div>

        <div className="downloads-section">
          <h3>📥 Download Your Documents</h3>
          <div className="download-buttons">
            <button 
              onClick={() => onDownload('resume')}
              className="btn btn-download"
            >
              📄 Download Tailored Resume
            </button>
            <button 
              onClick={() => onDownload('cover_letter')}
              className="btn btn-download"
            >
              ✉️ Download Cover Letter
            </button>
          </div>
          <p className="download-note">Documents are in DOCX format. You can edit them in Word or Google Docs.</p>
        </div>

        <div className="details-section">
          <div
            className="detail-header"
            onClick={() => toggleSection('agents')}
          >
            <h3>Agent Reasoning & Outputs {expandedSection === 'agents' ? '▼' : '▶'}</h3>
          </div>
          {expandedSection === 'agents' && (
            <div className="detail-content agent-trace-list">
              {agentEntries.length > 0 ? (
                agentEntries.map(([agentKey, agentData]) => (
                  <div className="agent-trace" key={agentKey}>
                    <div className="agent-trace-header">
                      <h4>{agentLabels[agentKey] || agentKey}</h4>
                      <span>{Number(agentData.execution_time || 0).toFixed(2)}s</span>
                    </div>
                    <div className="agent-trace-block">
                      <h5>Reasoning</h5>
                      <pre>{agentData.reasoning || 'No reasoning returned.'}</pre>
                    </div>
                    <div className="agent-trace-block">
                      <h5>Output</h5>
                      <pre>{formatAgentOutput(agentData.output)}</pre>
                    </div>
                  </div>
                ))
              ) : (
                <p>No specialist agent outputs were returned by the backend.</p>
              )}
            </div>
          )}
        </div>

        <div className="details-section">
          <div 
            className="detail-header"
            onClick={() => toggleSection('scores')}
          >
            <h3>📊 Component Scores {expandedSection === 'scores' ? '▼' : '▶'}</h3>
          </div>
          {expandedSection === 'scores' && (
            <div className="detail-content">
              {scoreRows.map(([label, score]) => (
                <div className="score-item" key={label}>
                  <span>{label}</span>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: scoreWidth(score) }}></div>
                  </div>
                  <span className="score-number">{formatScore(score)}{score === null || score === undefined ? '' : '/10'}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="details-section">
          <div 
            className="detail-header"
            onClick={() => toggleSection('improvements')}
          >
            <h3>💡 Improvement Suggestions {expandedSection === 'improvements' ? '▼' : '▶'}</h3>
          </div>
          {expandedSection === 'improvements' && (
            <div className="detail-content">
              {results.improvements && results.improvements.length > 0 ? (
                <ul className="improvements-list">
                  {results.improvements.map((improvement, index) => (
                    <li key={index}>{String(improvement)}</li>
                  ))}
                </ul>
              ) : (
                <p>No improvements suggested - your application looks great!</p>
              )}
            </div>
          )}
        </div>

        <div className="actions-section">
          <button 
            onClick={onNewApplication}
            className="btn btn-primary btn-large"
          >
            ➕ Create Another Application
          </button>
        </div>

        <div className="success-message">
          <p>Good luck with your application!</p>
        </div>
      </div>
    </div>
  )
}

export default ResultsDisplay
