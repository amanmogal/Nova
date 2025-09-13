#  **Notion Agent Monorepo Structure**

This document outlines the monorepo structure for the Notion Agent SaaS Platform.

##  **Directory Structure**

```
agent_notion/
├──  src/                    # Backend (FastAPI)
│   ├──  auth/              # Authentication & user management
│   ├──  api/               # API endpoints
│   ├──  models/            # Database models
│   ├──  services/          # Business logic
│   ├──  monitoring/        # Monitoring & analytics
│   └──  tools/             # Agent tools
├──  frontend/              # Frontend (Next.js)
│   ├──  src/
│   │   ├──  app/          # Next.js app router
│   │   ├──  components/   # React components
│   │   ├──  lib/          # Utilities
│   │   └──  types/        # TypeScript types
│   └──  public/
├──  shared/                # Shared code
│   ├──  types/            # Common TypeScript types
│   ├──  constants/        # Shared constants
│   └──  utils/            # Shared utilities
├──  deployment/           # Deployment configs
│   ├──  docker-compose.yml
│   ├──  Dockerfile.backend
│   └──  Dockerfile.frontend
├──  docs/                 # Documentation
├──  tests/                # Tests
└──  data/                 # Data storage
```

##  **Quick Start**

### **Prerequisites**
- Node.js 18+
- Python 3.12+
- Docker & Docker Compose
- Git

### **Installation**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent_notion
   ```

2. **Install dependencies**
   ```bash
   # Install root dependencies
   npm install
   
   # Install frontend dependencies
   cd frontend && npm install && cd ..
   
   # Install shared package dependencies
   cd shared && npm install && cd ..
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your credentials
   nano .env
   ```

4. **Start development servers**
   ```bash
   # Start both frontend and backend
   npm run dev
   
   # Or start individually
   npm run dev:backend  # Backend on http://localhost:8000
   npm run dev:frontend # Frontend on http://localhost:3000
   ```

##  **Development Workflow**

### **Available Scripts**

```bash
# Development
npm run dev              # Start both frontend and backend
npm run dev:backend      # Start backend only
npm run dev:frontend     # Start frontend only

# Building
npm run build            # Build both shared and frontend
npm run build:shared     # Build shared package
npm run build:frontend   # Build frontend

# Testing
npm run test             # Run all tests
npm run test:backend     # Run backend tests
npm run test:frontend    # Run frontend tests

# Linting
npm run lint             # Lint all code
npm run lint:backend     # Lint backend code
npm run lint:frontend    # Lint frontend code

# Cleaning
npm run clean            # Clean all builds
npm run clean:shared     # Clean shared package
npm run clean:frontend   # Clean frontend
```

### **Docker Development**

```bash
# Start all services with Docker
docker-compose up

# Start specific services
docker-compose up backend frontend

# Rebuild and start
docker-compose up --build

# Stop all services
docker-compose down
```

##  **Package Structure**

### **Shared Package (`shared/`)**
- **Types**: Common TypeScript interfaces and types
- **Constants**: Shared constants and configuration
- **Utils**: Shared utility functions

### **Frontend (`frontend/`)**
- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for components

### **Backend (`src/`)**
- **FastAPI** for API endpoints
- **SQLAlchemy** for database operations
- **LangGraph** for agent orchestration
- **ChromaDB** for vector storage

##  **Package Dependencies**

### **Frontend Dependencies**
```json
{
  "dependencies": {
    "@notion-agent/shared": "file:../shared",
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "next-auth": "^4.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.0.0"
  }
}
```

### **Shared Package Dependencies**
```json
{
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
```

##  **API Structure**

### **Backend API Endpoints**
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /api/auth/login` - User authentication
- `GET /api/users/profile` - User profile
- `POST /api/agent/chat` - Agent chat
- `GET /api/tasks` - Task management
- `GET /api/routines` - Routine management

### **Frontend Routes**
- `/` - Dashboard
- `/auth/login` - Login page
- `/auth/callback` - OAuth callback
- `/dashboard` - User dashboard
- `/tasks` - Task management
- `/routines` - Routine management
- `/settings` - User settings

##  **Configuration**

### **Environment Variables**
```bash
# Core API Keys
GOOGLE_API_KEY=your_google_api_key
NOTION_API_KEY=your_notion_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Notion Database IDs
NOTION_TASKS_DATABASE_ID=your_tasks_db_id
NOTION_ROUTINES_DATABASE_ID=your_routines_db_id

# Monitoring
GRAFANA_USERNAME=your_grafana_username
GRAFANA_API_KEY=your_grafana_api_key
GRAFANA_PROMETHEUS_URL=your_prometheus_url

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

##  **Testing**

### **Backend Testing**
```bash
cd src
python -m pytest tests/
```

### **Frontend Testing**
```bash
cd frontend
npm run test
```

### **E2E Testing**
```bash
npm run test:e2e
```

##  **Monitoring**

### **Metrics**
- Prometheus metrics available at `/metrics`
- Grafana Cloud integration for visualization
- Custom metrics for agent operations

### **Logging**
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation

##  **Deployment**

### **Production Deployment**
```bash
# Build all packages
npm run build

# Deploy to Google Cloud
gcloud run deploy notion-agent-backend --source .
gcloud run deploy notion-agent-frontend --source .
```

### **Staging Deployment**
```bash
# Deploy to staging environment
npm run deploy:staging
```

##  **Documentation**

- [Phase 5 Implementation Plan](./docs/PHASE_5_IMPLEMENTATION_PLAN.md)
- [Development Status](./docs/DEVELOPMENT_STATUS.md)
- [API Documentation](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)

##  **Contributing**

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

##  **License**

MIT License - see [LICENSE](./LICENSE) file for details. 