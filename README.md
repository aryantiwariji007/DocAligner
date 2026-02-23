# On-Premises Document Standards & Validation Platform

A secure, offline-capable platform for managing ODF document standards, validating documents, and enforcing compliance across folders.

## Features
- **ODF 1.2 Compliance**: Validates `.odt` files against strict ODF 1.2 specifications.
- **Standards Management**: Promote golden documents to Standards.
- **Inheritance**: Apply standards to Folders; documents inherit rules from parent folders.
- **Automated Validation**: Async processing using Celery to validate documents upon upload.
- **Audit Logging**: Full history of uploads, promotions, and assignments.
- **On-Premise**: Fully containerized with Docker, no cloud dependencies.

## Architecture
- **Frontend**: Next.js 13+ (App Router), TypeScript, Vanilla CSS.
- **Backend**: FastAPI, SQLModel (PostgreSQL), Celery (Redis).
- **Storage**: MinIO (S3 compatible).
- **Auth**: Keycloak (OIDC/JWT).
- **Processing**: ODFPy + LibreOffice (Headless).

## collaborative setup
1. **Prerequisites**: Docker & Docker Compose.
2. **Start Services**:
   ```bash
   cd docker
   docker-compose up -d --build
   ```
3. **Access**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001 (minio/minio123)
   - Keycloak: http://localhost:8080 (admin/admin)

## Development
- **Backend Local**:
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  uvicorn backend.app.main:app --reload
  ```
- **Frontend Local**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
