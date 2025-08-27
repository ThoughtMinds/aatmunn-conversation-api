# Aatmun - PoC

![Stack](https://skillicons.dev/icons?i=ubuntu,bash,py)

## [Features](./static/docs/Endpoints.md)


## Models

| Chat Model  | Embedding Model       |
|-------------|-----------------------|
| llama3.2:3b | nomic-embed-text:v1.5 |

Models are served through Ollama 

## Usage

The project is designed to run as docker containers with live reload.

> [!NOTE]
> Run this command on the first run to initialize


```bash
make init
```

![Init command](./static/images/init.svg)


Now simply run

```bash
make dev
```

![Dev command](./static/images/dev.svg)


This will use the [docker-compose.yml](./docker-compose.yml) and build a FastAPI container image based on [Dockerfile](./Dockerfile).

```bash
docker ps --format '{{.Names}}'
```

```
aatmunn-api
aatmunn-frontend
ollama
```

### Testing

You can run tests for the API using `newman`

```bash
make tests
```

![Test command](./static/images/test.svg)


## Development

### API

Get pipenv

```bash
pip install pipenv
```

Create a virtual environment

```bash
pipenv shell
```

Install packages with pipenv

```bash
pipenv install
```

### Frontend
Mount the local directory by uncommenting the following in [compose](./docker-compose.yml)

```yml
volumes:
    - ./frontend:/app
```

Install npm packages

```bash
cd frontend 
npm i --force
```

Run the React app

```bash
npm run dev
```

## Checklist
- [x] Update Collection for Newman
- [x] Add mock tables for Task Execution, Summarization data
- [x] Orchestrator
    - [x] Frontend
    - [x] Identify intent & invoke sub-graph
        - [x] Log Agent State
- [x] Summrization Agent
    - [x] Frontend
    - [x] Single Tool Call
    - [x] Chained Tool Call
    - [x] Content Moderation
        - [x] Fixed Output Schema
        - [x] Meaningful summary
        - [x] Integrate with flow
- [x] Task Execution Agent
    - [x] Frontend
    - [x] Single Tool Call
    - [x] Chained Tool Call
- [x] Chained Tool Call
    - [x] Implement
    - [x] Convert to Graph
    - [x] Frontend Support 
- [x] Test Framework
    - [x] Navigation
    - [ ] Summarization
    - [ ] Task Execution
- [x] Integration with Aatmunn API
    - [x] Read APIs
        - [ ] Integrate Navigation Options API
    - [x] Replace local data with APIs
    - [x] Explore other Read, Write API's
- [x] Add timestamp & processing time
- [ ] Log actions to DB
- [x] Colored logging for local dev
