# Aatmun - PoC

![Stack](https://skillicons.dev/icons?i=ubuntu,bash,py)


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
aatmun-api
aatmun-frontend
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
# install pipenv
pip install pipenv
```

Create a virtual environment

```bash
# create a pipenv shell/virtualenv
pipenv shell
```

Install packages with pipenv
```bash
# install packages
pipenv install
```

### R&D
All R&D has been documented as jupter [notebooks](./notebooks/). They can be explored by installing `jupter`

```bash
pip install jupyter
```

and run:

```bash
jupyter notebook
```

### Frontend
Mount the local directory by uncommenting the following in [comopose](./docker-compose.yml)

```yml
volumes:
    - ./frontend:/app
```

Install npm packages

```bash
cd frontend 
npm i --force
```

Run the React application

```bash
npm run dev
```

## Checklist
- [x] Update OpenAI schema for database -> navigation_intents
- [ ] Implement Summarization
- [ ] Implement Task Execution
- [ ] Test Framework
    - [x] Navigation
    - [ ] Summarization
    - [ ] Task Execution
- [ ] Add mock tables for Task Execution, Summarization data
- [x] Add Orchestrator Frontend
    - [ ] Orchestrator flow to identify intent and invoke sub-graph based on intent
