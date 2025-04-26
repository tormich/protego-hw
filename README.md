# Protego Health - Backend System

## Overview

This project is a comprehensive backend system that scrapes public drug data from DailyMed, performs analytics on the data, stores it in a PostgreSQL database, and exposes a CRUD API for accessing both raw and analyzed data.

### Key Features

- **Data Scraping**: Automated scraping of drug classes and drug information from DailyMed
- **Data Analysis**: Multiple analytics modules for analyzing drug data (NDC codes, classifications, names, etc.)
- **REST API**: Complete CRUD operations for all data models
- **Containerization**: Docker and Kubernetes support for easy deployment
- **Scheduled Jobs**: Automated scraping and analysis on configurable schedules

### Technology Stack

- **Backend**: Python 3.13
- **Web Framework**: FastAPI
- **Database**: PostgreSQL 17
- **ORM**: SQLAlchemy
- **Containerization**: Docker, Kubernetes
- **Package Management**: uv
- **Migration**: Alembic

## Architecture

The system consists of four main components:

1. **Database Service**: PostgreSQL database for storing all data
2. **Scraper Service**: Collects drug data from DailyMed and stores it in the database
3. **Analytics Service**: Processes the scraped data to extract insights
4. **API Service**: Exposes CRUD endpoints for accessing both raw and analyzed data

### System Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Scraper   │────▶│  Database   │◀────│  Analytics  │
│  (CronJob)  │     │ (PostgreSQL)│     │  (CronJob)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │     API     │
                    │   (FastAPI) │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Clients   │
                    └─────────────┘
```

### Data Flow

1. The Scraper service collects drug class and drug data from DailyMed
2. Data is stored in the PostgreSQL database
3. The Analytics service processes the data to generate insights
4. The API service provides access to both raw and analyzed data
5. Clients interact with the system through the API

## Setup and Installation

### Prerequisites

- Docker and Docker Compose (for local development)
- Kubernetes cluster (for production deployment)
- Python 3.13+ (for local development without Docker)

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydatabase
POSTGRES_PORT=5432
POSTGRES_HOST=db
API_PORT=8000
LOG_LEVEL=INFO
```

### Local Development with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/protego-hw.git
   cd protego-hw
   ```

2. Build and start the services:
   ```bash
   docker-compose up -d
   ```

3. Access the API at http://localhost:8000

4. Run the scraper manually (if needed):
   ```bash
   docker-compose run scraper
   ```

5. Run the analytics manually (if needed):
   ```bash
   docker-compose run analytics
   ```

### Kubernetes Deployment

1. Build and push the Docker images:
   ```bash
   docker build -t your-registry/protego-hw-api:latest -f api/Dockerfile .
   docker build -t your-registry/protego-hw-scraper:latest -f scraper/Dockerfile .
   docker build -t your-registry/protego-hw-analytics:latest -f analytics/Dockerfile .

   docker push your-registry/protego-hw-api:latest
   docker push your-registry/protego-hw-scraper:latest
   docker push your-registry/protego-hw-analytics:latest
   ```

2. Update the image references in the Kubernetes YAML files

3. Apply the Kubernetes configuration:
   ```bash
   kubectl apply -k k8s/
   ```

4. Access the API through the configured Ingress

## Usage

### API Endpoints

The API provides the following endpoints:

- **Drug Classes**:
  - `GET /drug-classes/`: List all drug classes
  - `GET /drug-classes/{id}`: Get a specific drug class
  - `POST /drug-classes/`: Create a new drug class
  - `PUT /drug-classes/{id}`: Update a drug class
  - `DELETE /drug-classes/{id}`: Delete a drug class

- **Drugs**:
  - `GET /drugs/`: List all drugs
  - `GET /drugs/{id}`: Get a specific drug
  - `POST /drugs/`: Create a new drug
  - `PUT /drugs/{id}`: Update a drug
  - `DELETE /drugs/{id}`: Delete a drug

- **Analytics**:
  - `GET /analytics/results/`: List all analytics results
  - `GET /analytics/ndc/`: List NDC analysis results
  - `GET /analytics/drug-classes/`: List drug class analysis results
  - `GET /analytics/names/`: List name analysis results
  - And more...

### Scheduled Jobs

- **Scraper**: Runs daily at midnight to collect new data
- **Analytics**: Runs every 2 days at 00:10 (10 minutes after the scraper) to analyze the data

## Development

### Project Structure

```
├── api/                # API service code
│   ├── routers/        # API route definitions
│   └── schemas/        # Pydantic schemas
├── analytics/          # Analytics service code
├── models/             # SQLAlchemy models
├── scraper/            # Scraper service code
├── k8s/                # Kubernetes configuration
├── docker-compose.yml  # Docker Compose configuration
└── README.md          # This file
```

### Adding New Features

1. **New Models**: Add new SQLAlchemy models in the `models/` directory
2. **Database Migrations**: Use Alembic to create migrations
   ```bash
   alembic revision --autogenerate -m "Add new model"
   alembic upgrade head
   ```
3. **New API Endpoints**: Add new routers in the `api/routers/` directory
4. **New Analytics**: Add new analyzers in the `analytics/` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.
