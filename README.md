# Channel Crossing Research Early Warnning
This is an application developed for the Channel Monitoring Project.
It aides in monitoring and alerting and reporting on activities and conditions on the Channel, with regard to situations where there is a risk of harm. It is a set of utilities that help study activities in order the reduce risk and harm of those crossing in hazardous routes.

## Overview
This is divided into three sections, Ingestion, Alerty and Reports and Monitoring.
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
