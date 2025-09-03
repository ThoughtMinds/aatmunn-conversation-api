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
- [x] Orchestrator
    - [x] Frontend
    - [x] Identify intent & invoke sub-graph
- [x] Summrization Agent
    - [x] Frontend
    - [x] Single & Chained Tool Call
    - [x] Content Moderation
    - [x] Meaningful summary
- [x] Task Execution Agent
    - [x] Frontend
    - [x] Single & Chained Tool Call
    - [ ] Rate limit chaining
    - [ ] User confirmation (yes/no) before execution
- [x] Test Framework
    - [x] Integrated test framework
        - [x] Navigation
        - [x] Summarization
        - [ ] Task Execution
- [x] Integration with Aatmunn API
    - [x] Read APIs
- [x] Logging
    - [x] Add timestamp & processing time
    - [x] Log actions to DB
    - [x] Colored logging