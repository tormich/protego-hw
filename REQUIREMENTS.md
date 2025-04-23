# Requirements

## 1. Scraper Service (Docker container)
- Scrape or pull structured data from a public source (Examples):
  - FDA drug labels from dailymed.nlm.nih.gov
  - GitHub repo data
  - Clinical trials from clinicaltrials.gov
- Save scraped data to PostgreSQL

## 2. Analysis Service (Docker container)
- Read data from DB:
  - Link
  - Time pulled
  - Data
- Perform basic analysis (Examples):
  - Count keyword mentions
  - Most frequent terms
  - Group/filter by condition, category, etc.
- Save results to DB

## 3. CRUD API
- FastAPI app exposing full CRUD for raw and analyzed data
- Include OpenAPI docs

## 4. Containers and Orchestrator
- Use dockers to run scraper, analysis, API, and DB as separate services
- Use K8S to orchestrate the dockers

## 5. Deliverables
- Github (mono) Repo
- README Include setup, execution and a short architecture overview
- After submission you'll walk through the architecture, answer questions, and code a small feature live

## Notes
- This task is your opportunity to show how you solve a real-world problem end-to-end
- If anything is unclear, make assumptions. Ask only if you must
- AI tools - Use is encouraged, but understand and review all code yourself
- You don't have to get to 100% completion

