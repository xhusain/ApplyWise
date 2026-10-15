import React, { useState } from 'react'

function JobInputForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    jobDescription: '',
    applicantName: '',
    applicantEmail: '',
    resumeFile: null
  })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (!['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
        setErrors(prev => ({
          ...prev,
          resumeFile: 'Please upload a PDF or DOCX file'
        }))
        e.target.value = ''
        return
      }
      setFormData(prev => ({
        ...prev,
        resumeFile: file
      }))
      setErrors(prev => ({
        ...prev,
        resumeFile: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.jobDescription.trim()) {
      newErrors.jobDescription = 'Job description is required'
    } else if (formData.jobDescription.length < 50) {
      newErrors.jobDescription = 'Job description must be at least 50 characters'
    }

    if (!formData.applicantName.trim()) {
      newErrors.applicantName = 'Name is required'
    }

    if (!formData.applicantEmail.trim()) {
      newErrors.applicantEmail = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.applicantEmail)) {
      newErrors.applicantEmail = 'Please enter a valid email'
    }

    if (!formData.resumeFile) {
      newErrors.resumeFile = 'Resume file is required'
    }

    return newErrors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const newErrors = validateForm()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setSubmitting(true)
    try {
      await onSubmit(formData)
      setFormData({
        jobDescription: '',
        applicantName: '',
        applicantEmail: '',
        resumeFile: null
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="form-container">
      <div className="form-layout">
        <div className="form-card">
          <h2>Create Your Job Application</h2>
          <p className="form-subtitle">Upload your resume and job description, and let AI handle the rest</p>

          <form onSubmit={handleSubmit} className="application-form">
            <div className="form-group">
              <label htmlFor="applicantName">Your Name</label>
              <input
                type="text"
                id="applicantName"
                name="applicantName"
                value={formData.applicantName}
                onChange={handleInputChange}
                placeholder="John Doe"
                disabled={submitting}
              />
              {errors.applicantName && <span className="error-text">{errors.applicantName}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="applicantEmail">Email Address</label>
              <input
                type="email"
                id="applicantEmail"
                name="applicantEmail"
                value={formData.applicantEmail}
                onChange={handleInputChange}
                placeholder="john@example.com"
                disabled={submitting}
              />
              {errors.applicantEmail && <span className="error-text">{errors.applicantEmail}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="resumeFile">Upload Resume</label>
              <div className="file-input-wrapper">
                <label htmlFor="resumeFile" className="file-upload-box">
                  <input
                    type="file"
                    id="resumeFile"
                    accept=".pdf,.docx,.doc"
                    onChange={handleFileChange}
                    disabled={submitting}
                  />
                  <span className="file-name">
                    {formData.resumeFile ? formData.resumeFile.name : 'Choose PDF or DOCX file'}
                  </span>
                </label>
              </div>
              {errors.resumeFile && <span className="error-text">{errors.resumeFile}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="jobDescription">Job Description</label>
              <textarea
                id="jobDescription"
                name="jobDescription"
                value={formData.jobDescription}
                onChange={handleInputChange}
                placeholder="Paste the job description here... (Company name, requirements, responsibilities, etc.)"
                rows={8}
                disabled={submitting}
              />
              {errors.jobDescription && <span className="error-text">{errors.jobDescription}</span>}
              <span className="char-count">{formData.jobDescription.length} characters</span>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-large"
              disabled={submitting}
            >
              {submitting ? 'Processing...' : 'Generate Application'}
            </button>
          </form>
        </div>

        <aside className="how-it-works-card">
          <h3>How It Works</h3>

          <div className="workflow-steps">
            <div className="workflow-step step-blue">
              <span className="step-number">1</span>
              <div>
                <h4>Job Finder</h4>
                <p>Analyzes the job posting and researches the company.</p>
              </div>
            </div>

            <div className="workflow-step step-teal">
              <span className="step-number">2</span>
              <div>
                <h4>Resume Tailor</h4>
                <p>Customizes your resume to match job requirements.</p>
              </div>
            </div>

            <div className="workflow-step step-sky">
              <span className="step-number">3</span>
              <div>
                <h4>Cover Letter Generator</h4>
                <p>Creates a personalized cover letter for the role.</p>
              </div>
            </div>

            <div className="workflow-step step-green">
              <span className="step-number">4</span>
              <div>
                <h4>Critic Agent</h4>
                <p>Reviews outputs and suggests improvements.</p>
              </div>
            </div>

            <div className="workflow-step step-orange">
              <span className="step-number">5</span>
              <div>
                <h4>Download Files</h4>
                <p>Download your tailored resume and cover letter instantly.</p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default JobInputForm
