# ApplyWise

ApplyWise is an AI-powered job application assistant. Upload a resume and
paste a job description to generate a tailored resume, a personalized cover
letter, quality scores, and a transparent execution summary from multiple
specialist agents.

The repository contains two implementations:

- A **Python/FastAPI + React** application for local development and the main
  demo.
- An **n8n workflow** that provides an alternative automation flow using an
  n8n webhook and Groq.

> **Important:** Never commit API keys, uploaded resumes, generated documents,
> or other personal information to GitHub. The included `.gitignore` excludes
> these files for new Git repositories.

## Features

- Extracts job title, company, requirements, skills, qualifications, and ATS
  keywords from a job description.
- Tailors resume content for the target role.
- Generates a personalized cover letter.
- Reviews the application package for quality, ATS compatibility, alignment,
  and readiness.
- Produces downloadable DOCX files.
- Displays agent outputs, processing steps, scores, and suggested improvements.
- Includes a separate n8n workflow for DOCX resume processing.

## Architecture

### Python application

The backend coordinates four specialist agents through a supervisor:

1. **Job Finder Agent** - analyzes the job description and extracts role and
   company context.
2. **Resume Tailor Agent** - aligns resume content with the target role.
3. **Cover Letter Agent** - generates a role-specific cover letter.
4. **Critic Agent** - evaluates quality, ATS alignment, and improvements.
5. **Supervisor Orchestrator** - coordinates the agents and generates DOCX
   documents.

### Main directories

```text
ApplyWise/
├── backend/
│   ├── agents/              # Specialist agents
│   ├── api/                 # FastAPI routes and application factory
│   ├── models/              # Pydantic schemas
│   ├── orchestrator/        # Supervisor orchestration
│   ├── services/            # LLM, document, and storage services
│   ├── utils/               # Resume parsing helpers
│   ├── config.py            # Environment-based settings
│   ├── main.py              # Backend entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React application
│   ├── package.json         # Node dependencies and scripts
│   └── vite.config.js       # Development proxy configuration
├── n8n workflow/
│   └── ApplyWise n8n Workflow.json
├── uploads/                 # Local uploaded resumes (ignored by Git)
└── outputs/                 # Generated documents (ignored by Git)
```

## Prerequisites

Install the following before starting:

- Python 3.10 or newer
- Node.js 18 or newer and npm
- A [Groq API key](https://console.groq.com/)
- A [Tavily API key](https://app.tavily.com/) for search/context tooling

## Local setup on Windows

Run these commands from the project root:

```powershell
cd "L:\AU\SEM-6\GenAI\Project\ApplyWise"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

If PowerShell blocks activation, either run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

or use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Configure environment variables

Create a local `.env` file in the project root by copying `.env.example`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder values with your real API keys.
`.env.example` is safe to commit because it contains no credentials.

Do not put real keys in `README.md`, source code, screenshots, or the n8n
workflow JSON. The backend loads `.env` automatically through
`pydantic-settings`.

## Run the Python/FastAPI application

Build the frontend first so FastAPI can serve its production files:

```powershell
cd frontend
npm run build
cd ..
```

Start the full application:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

Open:

- Application: <http://localhost:8000>
- Swagger API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

Basic workflow:

1. Enter the applicant name and email.
2. Upload a PDF or DOCX resume.
3. Paste the target job description.
4. Submit the form and wait for processing.
5. Review scores, agent outputs, and improvements.
6. Download the tailored resume and cover letter.

## Frontend development mode

For live frontend changes, use two terminals.

Terminal 1:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open <http://localhost:3000>. Vite proxies `/api` requests to the backend at
`http://localhost:8000`.

Useful frontend commands:

```powershell
npm run build
npm run lint
npm run preview
```

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check whether the service is running |
| `GET` | `/api/info` | Show application and endpoint information |
| `POST` | `/api/process` | Process a resume and job description |
| `GET` | `/api/results/{job_id}` | List generated files for a job |
| `GET` | `/api/download/{job_id}/{file_type}` | Download a generated document |
| `POST` | `/api/cleanup/{job_id}` | Remove local job files |

The `/api/process` endpoint expects multipart form data with:

- `job_description`
- `applicant_name`
- `applicant_email`
- `resume_file`

## n8n workflow

The workflow is stored at
`n8n workflow/ApplyWise n8n Workflow.json`.

To import it:

1. Open n8n.
2. Select **Workflows**, then **Import from File**.
3. Choose the workflow JSON file.
4. Create or select a Groq credential for the Groq HTTP Request nodes.
5. Review the webhook, HTTP Request, and response nodes before activating it.
6. Activate the workflow and copy the generated webhook URL.

The n8n flow expects a `multipart/form-data` request with a resume file field
named `resume` and applicant/job fields such as `name`, `email`, and
`job_description`. The n8n Vite configuration also contains a development
proxy for `http://localhost:5678`.

Do not export credentials with the workflow or commit n8n credential files.

## Testing and troubleshooting

Check that the environment is active and dependencies are installed:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

If the app cannot start, verify:

- `.env` exists in the project root.
- Both API keys are present and valid.
- `frontend\dist\index.html` exists after `npm run build`.
- Port `8000` is not already in use.
- The uploaded resume is a readable PDF or DOCX file.

## Upload this project to GitHub

### 1. Review files before publishing

The repository should include `README.md`, `.gitignore`, `.env.example`, and
`backend\requirements.txt`. The requirements file is intentionally tracked so
others can install the exact Python dependencies.

Do not include `.env`, `.venv`, `frontend\node_modules`, `uploads`, `outputs`,
or `run.md`. The `.gitignore` covers them, but always review the staging list.

### 2. Initialize Git and create the first commit

Run from the project root:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Initial commit"
```

Before committing, confirm that `git status` does not list API keys, resumes,
DOCX output files, `node_modules`, `.env`, or `run.md`. Confirm that
`.env.example` and `backend\requirements.txt` are present.

### 3. Create the GitHub repository

On GitHub:

1. Click **New repository**.
2. Enter a repository name such as `ApplyWise`.
3. Choose **Public** or **Private**.
4. Do not add another README, `.gitignore`, or license if this project already
   contains them.
5. Click **Create repository**.

### 4. Connect the local project and push

Replace `YOUR_USERNAME` with your GitHub username:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/ApplyWise.git
git remote -v
git push -u origin main
```

If you use GitHub CLI instead:

```powershell
gh auth login
gh repo create ApplyWise --private --source=. --remote=origin --push
```

### 5. Add repository metadata

After the first push, update the GitHub repository description and topics, for
example: `python`, `fastapi`, `react`, `vite`, `groq`, `n8n`, `generative-ai`,
and `job-application`.

## Security and privacy

This application processes resumes and personal contact information. Use
synthetic/sample data while demonstrating the project, restrict repository
visibility when appropriate, rotate a key immediately if it is ever exposed,
and avoid uploading production resumes to public repositories.

## License

No license has been selected yet. Add a `LICENSE` file before presenting this
repository as open source.
