# OPENAI-API Service
A module to provide endpoints for OpenAI API to mange end users.

# Run
In order to run the OPENAI-API, you can either use docker or run locally.
in both ways, you need to set your parameters.

## Run Docker
build the docker file inside src folder via:

```bash
cd src
docker build -t openai-api:tag .
```
then, run the created image and expose the specified port:
```bash
docker run -p PORTNUMBER:8051 --env-file ./YOUR_ENV_FILE openai-api:tag
```

## Run locally
Install requirements from requirement.txt file in the src folder via:
```bash
cd src
pip install -r requirements.txt
```
then run the following command:
```bash
YOUR_ENV=YOUR_VAL python3 app.py
```