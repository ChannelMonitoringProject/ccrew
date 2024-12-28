# Channel Crossing Research Early Warnning
This is an application developed for the Channel Monitoring Project.
It aides in monitoring and alerting and reporting on activities and conditions on the Channel, focused on situations where there is a risk of harm. It is a set of utilities that help study activities in order the reduce risk and harm of those crossing in hazardous routes.

## Setup
The following must be performed from the project's root directory.
Copy the `./env.docker` to `.env` 

```bash
cp env.docker .env
```

This will set the environment variables needed to run, including database logins, third party api keys, and the config environment.
You will need to at least provide the `AIS_STREAM_API_KEY` by editing the `.env` file and adding it.

```sh
POSTGRES_DB=ccrew_database
POSTGRES_USER=user
POSTGRES_PASSWORD=password
AIS_STREAM_API_KEY="API KEY"
ENVIRONMENT="docker"
```

the `ENVIRONMENT` variable sets the config the application will use. it can be "dev" or "docker", but is easily configured as  necessary, see "ccrew/config.py". setting to "dev", will use localhost for the database and redis addresses, whereas "docker" will use the docker host defined in the `docker-compose.yml` file ("redis" and "database").


## Run
You can deploy the dockerised application locally by running

```bash
docker compose up
```

This will build and run the application and the required services (database, redis, celery and flask)

After that, you should have the service endpoints exposed on port 8050,
`curl localhost:8050/ais/start` will start ingesting AIS position reports
`curl localhost:8050/ais/status` will retust some status information about the running ingestion task
`curl localhost:8050/ais/stop` will end the ingestion task

the `/ais/start` endpoint runs the ingestion task, this will populate a postgresql database, which you can query by using
```bash
psql --host=localhost --dbname=ccrew_database --username=user
```

and provide the password defined in the `.env` or `env.docker` file("password" by default).

```sql
select * from public.boat_postion_reports
```

### Development
**using tmuxinator**
To run the application in development, I have included a helper .tmuxinator.yml file, if you have tmux and tmuxinator install you can run
```bash
tmuxinator
```
to start the application in a development environment

**manually**

The application requires a database and a redis service to be running.
you can start those with docker-compose by running.
```bash
docker-compose up database redis
```

edit the `.env` file and set the environment to "dev".
```sh
export ENVIRONMENT="dev"
```

**start the celery application**
The workloads are managed by [celery](https://docs.celeryq.dev/en/stable/). You start the celery application by running (in another terminal)

```bash
export FLASK_DEBUG=1 # Optional
source .venv/bin/activate
celery --app ccrew.celery_app worker --loglevel DEBUG
```

Now the celery is ready to start accepting tasks, but it's not running any tasks yet.

**start the flask application**
There is another application, a flask application which serves as an interface to the celery tasks. To start it, run

```bash
export FLASK_DEBUG=1 # Optional
source .venv/bin/activate
python -m flask --app ccrew.flask_app run
```

you can now start the celery tasks by hitting the relevant endpoints.

Currently, only one task is fully implemented, the AIS Stream listener, which updates boat entries in the database. 

You can now use

```bash
curl localhost:5000/ais/start
curl localhost:5000/ais/status
curl localhost:5000/ais/stop
```

to start and stop the task and query it's status


## Overview
This is divided into three sections, Ingestion, Alerts and Reports and Monitoring.
It is a Celery Task based Application with a Flask based REST Api which is divided nto Flask Blueprints


## Ingestions
This is in charge of collecting data, the ingestion is composed of Celery tasks, each responsible for retrieving data from a source, storing it in the database and updating any relevant state

### AIS Stream Task
This is a long running task which sits on a websocket connection to AIS Stream. 
It handles BoatPositionReports. It stores a position report for each boat in the region in intervals of no less then 15 seconds apart.
It also updates a state in the redis by updating it in that interval.

### Weather Data Task
This will store weather data at regular intervals (every hour) and store a update the redis state with the fortcast for the weak.

### Aircraft Data Task
TBD probably similar to AIS Stream Task


## Alerts

### Rule based alerts

### Daily weather forecast alert

## Report and monitoring

### Current State map

### Weather Report

### Historic State Map

## Setup

This application uses an SQL Database and a Redis database
Workloads are done using Celery which manages tasks
Tasks could be long running tasks such as ingesting a stream of boat position reports from a websocket, scheduled ingestion tasks such as hourly weather report. They could also be reporting and alerting tasks such as daily weather forecast report, or priodict alert dispatch.

The Celery application, defined in "ccrew/celery_app.py", runs in its own container, seperate from the frontend flask application. they communicate with eatchother using redis (in memory key/value database), this is defined in "config.py"

reports or periodic alerts and status updates




