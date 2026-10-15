import React from 'react'

function ProcessingStatus({ phases, formData }) {
  return (
    <div className="processing-container">
      <div className="processing-card">
        <h2>⏳ Processing Your Application</h2>
        
        <div className="applicant-info">
          <p><strong>Applicant:</strong> {formData?.applicantName}</p>
          <p><strong>Email:</strong> {formData?.applicantEmail}</p>
          <p><strong>Resume:</strong> {formData?.resumeFile?.name}</p>
        </div>

        <div className="phases-container">
          {phases.map((phase, index) => (
            <div key={index} className={`phase-item phase-${phase.status}`}>
              <div className="phase-icon">{phase.icon}</div>
              <div className="phase-content">
                <h3>{phase.name}</h3>
                <div className="phase-status">
                  {phase.status === 'pending' && <span className="status-badge pending">Pending</span>}
                  {phase.status === 'running' && <span className="status-badge running">Running</span>}
                  {phase.status === 'completed' && <span className="status-badge completed">✓ Completed</span>}
                  {phase.status === 'failed' && <span className="status-badge failed">Failed</span>}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="progress-bar">
          <div className="progress-fill" style={{
            width: `${(phases.filter(p => p.status === 'completed').length / phases.length) * 100}%`
          }}></div>
        </div>

        <p className="processing-message">
          Please wait while AI processes your application...
        </p>
      </div>
    </div>
  )
}

export default ProcessingStatus
