# ApplyWise

ApplyWise is an AI-powered job application assistant that transforms a
candidate's existing resume and a target job description into a tailored
application package.

It analyzes the job description, adapts the resume to the target role,
generates a personalized cover letter, and evaluates the resulting documents
for quality and job alignment. The project includes both a Python web
application and an equivalent n8n automation workflow.

## Highlights

- Job description analysis and ATS keyword extraction
- Resume tailoring for a specific position
- Personalized cover-letter generation
- Quality, alignment, and readiness scoring
- Downloadable DOCX resume and cover-letter files
- Visible agent execution results and improvement suggestions
- FastAPI backend with a React frontend
- Importable n8n workflow for an automation-based deployment

## How it works

The Python application uses a supervisor to coordinate four specialist agents:

| Component | Responsibility |
| --- | --- |
| Job Finder Agent | Extracts the role, company context, responsibilities, skills, and qualifications from the job description |
| Resume Tailor Agent | Aligns resume content with the target role without inventing candidate experience |
| Cover Letter Agent | Produces a role-specific cover letter using the job and candidate information |
| Critic Agent | Reviews the application package and reports quality, ATS, alignment, and improvement metrics |
| Supervisor Orchestrator | Coordinates the agents, combines their results, and generates the output documents |

### Processing flow

```text
Resume + Job Description
            |
            v
    Job Finder Agent
            |
            v
    Resume Tailor Agent ----> Tailored Resume
            |
            v
    Cover Letter Agent ------> Cover Letter
            |
            v
       Critic Agent ---------> Scores and Improvements
            |
            v
      Application Package
```

## Technology stack

- **Backend:** Python, FastAPI, Pydantic
- **Frontend:** React, Vite, Tailwind CSS
- **Language model:** Groq
- **Search and research:** Tavily
- **Document generation:** python-docx
- **Resume parsing:** PyPDF2 and DOCX processing
- **Automation alternative:** n8n

## Repository structure

```text
ApplyWise/
├── backend/
│   ├── agents/              # Specialist AI agents
│   ├── api/                 # FastAPI application and routes
│   ├── models/              # Pydantic data models
│   ├── orchestrator/        # Supervisor orchestration
│   ├── services/            # LLM, document, and storage services
│   ├── utils/               # Resume parsing utilities
│   ├── config.py            # Environment-based configuration
│   ├── main.py              # Backend entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React source code
│   ├── package.json         # Frontend scripts and dependencies
│   └── vite.config.js       # Vite development configuration
├── n8n workflow/
│   └── ApplyWise n8n Workflow.json
├── .env.example             # Configuration template
└── .gitignore
```

Generated resumes, uploaded files, local environment files, and dependency
folders are intentionally excluded from version control.

## Requirements

Before installing ApplyWise, ensure the following are available:

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- A Groq API key
- A Tavily API key

API keys can be created from the [Groq Console](https://console.groq.com/)
and the [Tavily Dashboard](https://app.tavily.com/).

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/<owner>/<repository>.git
cd ApplyWise
```

Create a Python virtual environment and install the backend dependencies.
On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Install the frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Configuration

Create a local `.env` file from the included template:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Add valid credentials to `.env`:

```dotenv
GROQ_API_KEY=replace_with_a_groq_api_key
TAVILY_API_KEY=replace_with_a_tavily_api_key
```

The `.env` file must remain local and must not be committed to a public
repository. The backend loads these values through `pydantic-settings`.

## Running the application

The production-style application serves the built React frontend from FastAPI.
Build the frontend before starting the backend:

```bash
cd frontend
npm run build
cd ..
```

Start the backend from the repository root:

On Windows:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

On macOS or Linux:

```bash
./.venv/bin/python backend/main.py
```

The application is available at:

- Web interface: <http://localhost:8000>
- Interactive API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

### Frontend development mode

For frontend development, run the backend and Vite development server in
separate terminals:

```bash
cd frontend
npm run dev
```

The development interface is available at
<http://localhost:3000>. Vite proxies API requests to the FastAPI server at
`http://localhost:8000`.

Available frontend commands:

```bash
npm run dev
npm run build
npm run lint
npm run preview
```

## Using the application

1. Open the web interface.
2. Enter the applicant's name and email address.
3. Upload a PDF or DOCX resume.
4. Paste the target job description.
5. Submit the application for processing.
6. Review the tailored resume, cover letter, scores, agent results, and
   improvement suggestions.
7. Download the generated DOCX files.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns the service health status |
| `GET` | `/api/info` | Returns application and endpoint information |
| `POST` | `/api/process` | Processes a resume and job description |
| `GET` | `/api/results/{job_id}` | Lists files generated for a job |
| `GET` | `/api/download/{job_id}/{file_type}` | Downloads a generated document |
| `POST` | `/api/cleanup/{job_id}` | Removes local files for a job |

The `/api/process` endpoint accepts `multipart/form-data` with these fields:

- `job_description`
- `applicant_name`
- `applicant_email`
- `resume_file`

## n8n workflow

An alternative workflow is available in
[`n8n workflow/ApplyWise n8n Workflow.json`](n8n%20workflow/ApplyWise%20n8n%20Workflow.json).

To use it:

1. Open an n8n instance.
2. Import the JSON file from **Workflows > Import from File**.
3. Configure the Groq credential used by the HTTP Request nodes.
4. Review the webhook and response settings.
5. Activate the workflow and use its generated webhook URL.

The workflow expects a `multipart/form-data` request containing:

- A resume file in a field named `resume`
- Applicant name in `name`, `applicant_name`, or `applicantName`
- Applicant email in `email`, `applicant_email`, or `applicantEmail`
- Job description in `job_description`, `jobDescription`, or `jd`

The n8n workflow processes DOCX resumes and uses Groq for the agent stages.
Credentials should be configured in n8n rather than stored in the exported
workflow file.

## Data and privacy

Resumes and generated application documents may contain personally
identifiable information. Use sample data for demonstrations, do not commit
personal documents to source control, and review the privacy policies of any
external AI or search services used with this application.

The following paths are ignored by default:

```text
.env
.venv/
frontend/node_modules/
frontend/dist/
uploads/
outputs/
*.docx
*.pdf
run.md
```

## Development

Python dependencies are pinned in
[`backend/requirements.txt`](backend/requirements.txt). The frontend
dependencies and scripts are defined in
[`frontend/package.json`](frontend/package.json).

Before submitting changes, run the relevant checks:

```bash
cd frontend
npm run lint
npm run build
```

## License

No license has been specified for this project yet. A license should be added
before redistributing the software or accepting external contributions.
