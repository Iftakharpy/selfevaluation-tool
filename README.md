- [Project info](#project-info)
  - [Additional info:](#additional-info)
  - [Frontend pages](#frontend-pages)
  - [Production environment setup guide](#production-environment-setup-guide)
  - [Development environment setup guide](#development-environment-setup-guide)
  - [Development using docker compose - supports auto reload both in frontend and backend](#development-using-docker-compose---supports-auto-reload-both-in-frontend-and-backend)
  - [Running tests](#running-tests)
  - [Test for production setup](#test-for-production-setup)
  - [Manual process](#manual-process)
    - [FastAPI backend](#fastapi-backend)
    - [React Frontend](#react-frontend)


# Project info

This project is separated in two parts UI and API for development ease. These are:
1. FastAPI backend serves the HTTP endpoints.
2. React UI which communicates with the FastAPI endpoints.

> Current implemented functionalities of the API's and UI can be seen by running the project with docker following the steps in the [production](#production-environment-setup-guide) or [development](#development-environment-setup-guide).

## Additional info:
- [SRS](./SRS.md)
- [Implementation details](./ImplementationSection.md)



## Frontend pages
Implementation reference: https://www.16personalities.com/
- navbar, 

- Home
- Survey
  - Edit/create/delete - for teachers
  - Once created can't be modified
  - Take survey - with link provided by teachers

- Courses - only for teachers
  - Questions

- Result - view only for teachers and students
  - there are only 3 results for now
  - 


## Production environment setup guide
This project is set up to run in production using docker, which will handle restarts when the host machine reboots or the containers crashes in case of errors.

Requirements:
1. A VPS with Linux OS
2. Docker daemon and cli installed on the

> Info: In the production nginx handle all the incoming requests and forwards any request going to `/api/*` or `/docs/*` or `/openapi.json` to the FastAPI backend. And other requests are assumed to be for the static files which nginx serves from the artifacts of `npm run build` command. If the resource for those request not found nginx will simply reply with HTTP 404 status code to indicate file not found error.

Steps to run the server:
1. Transfer all the files of the directory where `README.md` file is or clone the repository to the Linux Server via any means(eg. SSH, FTP, etc.)
2. Before running the following steps the `working directory` or `pwd` should be as instructed in previous step or where the the contents of the project were copied
3. `docker compose up -d` this will build the images and run the two containers
4. Now, you can visit `http://{server_ip}:80` to see the UI and interact with it using any web browser.
5. Logs can be seen using docker command.
6. Nginx specific logs like error/access logs can be seen via connecting shell to the nginx container using docker.


> Note: System admin should take measure and set up firewall rules after setting up the server. This is out of the scope of this Project so I am not going to discuss about security here.


## Development environment setup guide

## Development using docker compose - supports auto reload both in frontend and backend
Before running these commands Go to the directory where your project is for me it's `C:\Users\iftak\Desktop\jamk\2025 Spring\00-self-evaluation-tool\`. You can use docker desktop for easy log checking and other stats.

```bash
docker compose -f docker-compose.dev.yml up --build # If any dockerfile is changed and required for the first time
docker compose -f docker-compose.dev.yml up -d # after first build
docker compose -f docker-compose.dev.yml down # teardown
docker compose -f docker-compose.dev.yml down -fv # teardown and clean up volumes
```

## Running tests
```bash
docker compose -f docker-compose.test.yml up -d --build # Check docker desktop container logs
docker compose -f docker-compose.test.yml down -fv # teardown
```

## Test for production setup
```bash
docker compose up -d --build # Check docker desktop container logs
docker compose down # teardown but keeps the volumes
```


## Manual process

### FastAPI backend

1. Install anaconda/pyenv/venv to manage python environment
3. `conda create -n env_api python=3.13.3` creates conda environment for the project
4. `conda activate env_api` activates the created environment
5. Before running the following steps the `working directory` or `pwd` should be `./api`.
6. `pip install -r requirements.txt` instals the required packages for the project
7. `fastapi dev` runs the API and reloads the server when files changes in the app directory
8. Now, you can visit `http://localhost:8000` to see the API endpoints and try out the endpoints
9. To run tests for api endpoints. Run `pytest` or `pytest -n auto` or `pytest -n 0` from `./api` directory. Note: parallel tests are very fragile keeps throwing errors.

### React Frontend

1. Before running the following steps the `working directory` or `pwd` should be `./ui`
2. Note: During the development the `node:22` version was used, so keeping the same version will avoid unexpected errors
3. `npm install` will install the node packages
4. `npm run dev` will run the vite server for the UI with HMR
5. Since the FastAPI is being ran on port `8000` you will have to update the `BASE_URL` in [`./ui/src/services/api.ts`](./ui/src/services/api.ts#L6) file accordingly.
6. Now, you can visit `http://localhost:5173` to see the UI and interact with it.
