# ALET Locally Hosted LLMs Workshop 
This workshop details how to set up a locally hosted Large Language Model for personal use. 

In this particular workshop, we will be leveraging the Llama 4 model to analyze server log files. 

_Table of Contents_ 
1. [Utilized Tools](#utilized-tools)
    1. Lists and describes the tools utilized for this workshop 
2. [Installation Instructions](#installation-instructions)
    1. Provides links to install the required tools 
3. [Starting the Docker Containers](#starting-the-docker-containers)
    1. Details how to spin up the Docker containers 
4. [Downloading a LLM](#downloading-a-llm-from-ollama)
    1. Details the process for downloading a LLM from Ollama 
5. [Running the Web Interface](#running-the-web-interface)
    1. Provides instructions on running the Streamlit application within Docker 
6. [Tl;dr Running Instructions](#tldr-running-instructions)
    1. A quickstart to get the project up and running 

## Utilized Tools 
- **Docker (required)**
    - Docker will be utilized to containerize and serve Ollama, the Large Language Model hosting service
    - In addition, Docker will be utilized to containerize the Streamlit Python application
- Ollama (Optional)
    - Ollama is a LLM hosting service used to serve LLMs to various applications 
    - You can install Ollama locally, but for this workshop we will utilize Docker containers 
    - Ollama is just worth mentioning as a tool in general because it allows you to download and experiment with several open source LLMs


## Installation Instructions 
### Docker (Required)
[Docker Desktop](https://docs.docker.com/get-started/introduction/get-docker-desktop/)
- Follow the download instructions for your Operating System 

### Ollama (Optional)
[Ollama Download](https://ollama.com/download)
- Follow the instructions for your operating system 

Ollama contains a large collection of open-source [vision and language models](https://ollama.com/search). All of the models listed are free to use both locally and in an application. For the purposes of this workshop, we will utilize Docker to host Ollama, but if you are interested in inspecting a model (for example, Gemma 3) locally, you can follow the below instructions to download and run the model after installing Ollama: 

```
# Run the following commands from a terminal after installing Ollama. 
# This will download and run the Gemma 3 model. This model is ~3.5GB to download so it may take a minute
ollama run gemma3:latest
```

## Starting the Docker Containers
*Docker Desktop must be installed before running the following commands*
First you will have to build the docker containers for this workshop. To do so, run the following command from the root directory of the repository (the same location as this README): 
```
docker compose up -d --build
```

This will start the containers in a "detached state" so that they continue running after the docker command executes and will free up your terminal. 

To verify that Docker pulled the Ollama container properly, built the Streamlit container and that they are running, issue the following commands from the terminal: 
```
docker compose logs ollama 
docker compose logs streamlit_app
```

If you do not see an error in the terminal output, everything is working properly and you can proceed to the next step. 

**Note: to stop the containers if they are running in a detached state, run the following command from the terminal:**
```
docker compose down 
```

## Downloading a LLM from Ollama 
In order to work with the Streamlit Web Interface, we need to pull a large language model locally. 

For this workshop, we will be using the open-sourced Gemma3 model from Google. This model is fairly lightweight, only around 3.5GB. For comparison the latest, smallest, Llama 4 model (Llama4 Scout) is 65GB. It is likely that Llama 4 will give more accurate outputs but for the purpose of this workshop we will use the smaller model with less parameters. 

To pull Gemma3 from Ollama so that we can work with it locally, issue the following command from the terminal: 
```
docker exec ollama ollama pull gemma3:latest
```

This will take a few minutes to download most likely. 

### Downloading an Embedding model from Ollama 
We will also need a separate embedding model for working with the uploaded documents and user prompts. 

We will be using the `nomic-embed-text` model from Ollama for this workshop. To pull this model, run the following command from your terminal: 

```
docker exec ollama ollama pull nomic-embed-text
```

### Running Gemma3
It is also possible to run Gemma3 from inside the docker container. You simply have to attach to the container and issue the Ollama run command. To do this, run the following commands from the terminal: 

```
docker exec -it ollama bash 
ollama run gemma3:latest
```

The first command gives you an interactive terminal in the terminal and runs the bash command. 

The second command spins up the Gemma3 model from Ollama and allows you to interact with the model directly using a CLI. 

## Running the Web Interface 
After you have verified the containers have built properly, you can run them again and access the Streamlit app in your browser. 

First, run the docker compose command again (*if the containers aren't already running*):
```
docker compose up --build 
```

You should see the `http://0.0.0.0:8501` in the terminal. Navigate to this link to view the Streamlit application. 

### How to Use the Application
Will fill out once I'm finished with the app. 

## Tl;dr Running Instructions 
Just list all of the required commands here for running the entire project. 