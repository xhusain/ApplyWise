import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './styles/index.css'
import JobInputForm from './components/JobInputForm'
import ProcessingStatus from './components/ProcessingStatus'
import ResultsDisplay from './components/ResultsDisplay'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('Render error:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="app-container">
          <main className="app-main">
            <div className="error-container">
              <div className="error-card">
                <h2>Something went wrong</h2>
                <p>{this.state.error.message}</p>
                <button onClick={() => window.location.reload()} className="btn btn-primary">
                  Reload
                </button>
              </div>
            </div>
          </main>
        </div>
      )
    }

    return this.props.children
  }
}

function App() {
  const [currentStep, setCurrentStep] = useState('input')
  const [formData, setFormData] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [processingPhases, setProcessingPhases] = useState([])

  const toText = (value, fallback) => {
    if (typeof value === 'string' && value.trim()) return value
    if (typeof value === 'number') return String(value)
    return fallback
  }

  const toScore = (value) => {
    const score = Number(value)
    return Number.isFinite(score) ? Math.max(0, Math.min(10, score)) : null
  }

  const normalizeResults = (apiData) => {
    if (apiData.status && apiData.status !== 'completed') {
      throw new Error(apiData.error || apiData.message || 'Processing failed')
    }

    if (!hasGeneratedDocuments(apiData)) {
      throw new Error('Processing finished, but the generated resume and cover letter were not confirmed by the backend.')
    }

    const rawScores = apiData.component_scores && typeof apiData.component_scores === 'object'
      ? apiData.component_scores
      : {}

    const improvements = Array.isArray(apiData.improvements)
      ? apiData.improvements
      : typeof apiData.improvements === 'string' && apiData.improvements.trim()
        ? [apiData.improvements]
        : []

    return {
      job_id: toText(apiData.job_id, 'unknown'),
      status: apiData.status || 'completed',
      quality_score: toScore(apiData.quality_score),
      ready_for_submission: Boolean(apiData.ready_for_submission),
      job_title: toText(apiData.job_title, 'Unknown Position'),
      company: toText(apiData.company, 'Unknown Company'),
      component_scores: {
        resume: toScore(rawScores.resume),
        cover_letter: toScore(rawScores.cover_letter),
        ats_compatibility: toScore(rawScores.ats_compatibility),
        job_alignment: toScore(rawScores.job_alignment)
      },
      improvements,
      agent_outputs: apiData.agent_outputs && typeof apiData.agent_outputs === 'object'
        ? apiData.agent_outputs
        : {},
      execution_log: Array.isArray(apiData.execution_log) ? apiData.execution_log : []
    }
  }

  const hasGeneratedDocuments = (apiData) => {
    return Boolean(
      apiData?.status === 'completed' &&
      apiData?.documents?.resume &&
      apiData?.documents?.cover_letter
    )
  }

  // Handle browser back button
  useEffect(() => {
    const handlePopState = () => {
      setCurrentStep('input')
      setFormData(null)
      setJobId(null)
      setResults(null)
      setError(null)
      setProcessingPhases([])
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const handleSubmit = async (data) => {
    let phaseInterval = null

    try {
      setCurrentStep('processing')
      setFormData(data)
      setError(null)
      setProcessingPhases([
        { name: 'Analyzing Job Description', status: 'running', icon: '🔍' },
        { name: 'Tailoring Resume', status: 'pending', icon: '📄' },
        { name: 'Generating Cover Letter', status: 'pending', icon: '✉️' },
        { name: 'Quality Review', status: 'pending', icon: '🔎' },
        { name: 'Creating Documents', status: 'pending', icon: '📝' }
      ])

      const formDataToSend = new FormData()
      formDataToSend.append('job_description', data.jobDescription)
      formDataToSend.append('applicant_name', data.applicantName)
      formDataToSend.append('applicant_email', data.applicantEmail)
      formDataToSend.append('resume_file', data.resumeFile)

      let currentPhase = 0
      phaseInterval = setInterval(() => {
        if (currentPhase < 4) {
          setProcessingPhases(prev => {
            const updated = [...prev]
            updated[currentPhase].status = 'completed'
            if (currentPhase + 1 < updated.length) {
              updated[currentPhase + 1].status = 'running'
            }
            return updated
          })
          currentPhase++
        }
      }, 2000)

      const response = await axios.post('/api/process', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      clearInterval(phaseInterval)
      phaseInterval = null

      console.log('API Response:', response.data)
      window.localStorage.setItem('lastApiResponse', JSON.stringify(response.data))

      const apiData = response.data
      setJobId(apiData.job_id)
      const resultsData = normalizeResults(apiData)

      setProcessingPhases(prev =>
        prev.map(phase => ({ ...phase, status: 'completed' }))
      )

      console.log('Results object:', resultsData)
      setResults(resultsData)
      setCurrentStep('results')

    } catch (err) {
      if (phaseInterval) {
        clearInterval(phaseInterval)
      }

      console.error('Full error:', err)
      window.localStorage.setItem('lastApiError', JSON.stringify({
        message: err.message,
        response: err.response?.data || null
      }))
      setError(err.response?.data?.error || err.message || 'Failed to process application')
      setCurrentStep('error')
      setProcessingPhases(prev =>
        prev.map(phase => ({ ...phase, status: phase.status === 'running' ? 'failed' : phase.status }))
      )
    }
  }

  const handleDownload = async (fileType) => {
    try {
      const response = await axios.get(
        `/api/download/${jobId}/${fileType}`,
        { responseType: 'blob' }
      )

      const url = window.URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `${fileType}.docx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Failed to download file: ' + err.message)
    }
  }

  const handleNewApplication = () => {
    setCurrentStep('input')
    setFormData(null)
    setJobId(null)
    setResults(null)
    setError(null)
    setProcessingPhases([])
  }

  return (
    <ErrorBoundary>
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <h1>ApplyWise</h1>
          <p>From Job Post to Polished Application</p>
        </div>
      </header>

      <main className="app-main">
        {currentStep === 'input' && (
          <JobInputForm onSubmit={handleSubmit} />
        )}

        {currentStep === 'processing' && (
          <ProcessingStatus phases={processingPhases} formData={formData} />
        )}

        {currentStep === 'results' && results && (
          <ResultsDisplay 
            results={results}
            onDownload={handleDownload}
            onNewApplication={handleNewApplication}
          />
        )}

        {currentStep === 'error' && (
          <div className="error-container">
            <div className="error-card">
              <h2>❌ Processing Failed</h2>
              <p>{error}</p>
              <button onClick={handleNewApplication} className="btn btn-primary">
                Try Again
              </button>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>ApplyWise   |   Hussain Abdullah - 231999</p>
      </footer>
    </div>
    </ErrorBoundary>
  )
}

export default App
