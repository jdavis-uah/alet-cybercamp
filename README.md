# ALET Locally Hosted LLMs Workshop 
This workshop details how to set up a locally hosted Large Language Model for personal use. 

In this particular workshop, we will be leveraging the Gemma model to analyze server log files. 

First clone the repo by running the following command from a terminal: 
```
git clone https://github.com/jdavis-uah/alet-cybercamp.git
```

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
ollama run gemma3:1b
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

**Note: If the containers are not running in a detached state:**
You may have to issue the `ctrl+c` command to gain access back to the terminal and then run the `docker compose down` command to stop the containers.

## Downloading a LLM from Ollama 
In order to work with the Streamlit Web Interface, we need to pull a large language model locally. 

For this workshop, we will be using the open-sourced Gemma3:1b model from Google. This model is fairly lightweight, only around 815MB. For comparison the latest, smallest, Llama 4 model (Llama4 Scout) is 65GB. It is likely that Llama 4 will give more accurate outputs but for the purpose of this workshop we will use the smaller model with less parameters. 

**Note: Be sure your containers are running by executing `docker compose up -d --build` again in the terminal if you stopped them after checking the logs**

To pull the 1B model from Ollama run the following command from the terminal: 
```
docker exec ollama ollama pull gemma3:1b
```

`1b` here refers to the number of parameters of the model. The baseline Gemma model has 4 billion parameters whereas the 1b model has 1 billion parameters.

**NOTE: If you have access to a GPU and a lot of system memory, you can experiment with the Gemma3:latest model.**

We are using the Gemma3:1b model for this workshop because of constrained hardware resources. 
You may want to experiment with Gemma3:latest, the largest of the Gemma3 models. 
This model will be more accurate, but will also take longer to process queries. 
To pull Gemma3 from Ollama so that we can work with it locally, issue the following command from the terminal: 
```
docker exec ollama ollama pull gemma3:latest
```

This will take a few minutes to download most likely. 

We can also experiment with a much more lightweight model, TinyLlama. This model is designed to fit on less powerful devices and requires less compute. As a tradeoff, it is more prone to generate erroneous responses. To download the TinyLlama model, run the folling command from the terminal: 
```
docker exec ollama ollama pull tinyllama
```

**NOTE: If you wish to use Gemma3:latest or TinyLlama, follow the [instructions below](#changing-the-llm-used) to change the LLM used**

### Running Gemma3
It is also possible to run Gemma3 from inside the docker container. You simply have to attach to the container and issue the Ollama run command. To do this, run the following commands from the terminal: 

```
docker exec -it ollama bash 
ollama run gemma3:1b
```

The first command gives you an interactive terminal in the terminal and runs the bash command. 

The second command spins up the Gemma3 model from Ollama and allows you to interact with the model directly using a CLI. 

## Running the Web Interface 
After you have verified the containers have built properly, you can run them again and access the Streamlit app in your browser. 

First, run the following commands to start the containers without detaching. This will allow us to inspect the output from the Docker containers in the terminal.
```
docker compose down 
docker compose up
```

Running this command without the `-d` flag keeps the shell open to the docker containers. 

You should see the `http://0.0.0.0:8501` in the terminal. Navigate to this link to view the Streamlit application. 

**Note: On Windows systems, `http://0.0.0.0:8501` may not resolve. If you encourter this issue, navigate to `http://localhost:8501` instead.**

### How to Use the Application
First, you will need to upload a CSV file using the web application file loader. 

On upload, the application will embed the contained information. This is a computationally intensive process and may take some time. You can see the progress of the embeddings in the terminal output window. 

After the embeddings are computed, an LLM chat engine will be constructed for the uploaded file. You can now begin asking questions about the file and inspect the LLM responses. 

### Changing the LLM Used 
By default, the application uses the Gemma3:1b model for LLM processing. If you want to experiment with a different model, open the `config.toml` file and change the `LLM_MODEL_NAME` variable from `"gemma3:1b"` to `"gemma3:latest"` or `"tinyllama"`. 

You will have to rebuild and restart the application after making this change. You can do this by issuing the following commands in the terminal: 
```
docker compose down 
docker compose up --build 
```

### Changing the Number oF CSV Rows Processed 
By default, the application will process all of the rows contained in your CSV file. If you need to limit the number of rows being processed for performance reasons, open the `config.toml` file and find the `PROCESSING_ROW_LIMIT` variable. Setting the value of this variable to any number greater than 0 will instruct the application to only read that number of rows from the uploaded CSV file. I.e. `PROCESSING_ROW_LIMIT=100` will only read the first 100 rows from the uploaded CSV file. 

To reflect this change, you will have to rebuild and restart the application with the following commands in the terminal: 
```
docker compose down 
docker compose up --build 
```

### Note About Retrieval Augmented Generation
For this workshop, we are limited by hardware constraints. As such, when you submit a prompt to the model, the retrieval augmented generation (RAG) process only pulls back a limited number of relevant documents from the CSV file. 

These "relevant documents" are retrieved from an in-memory RAG database and their similarity is scored based on the contents of your prompt to the LLM. The term "documents" in this case refers to a vectorized representation of a row in the CSV file you have uploaded. These vectorized representations of the data in your CSV file is compared to a vectorized representation of your prompt to a model, and the top k similar documents are retrieved from the in-memory RAG database and passed to the model alongside your prompt. 

This highlights a limitation of running LLMs locally, unless you have extremely powerful hardware. Since we are resource constrained (compared to Google or OpenAI), we can only retrieve a small amount of relevant information compared to the massive scale at which these companies can retrieve data. As such, you may notice that the generated response does not include the entire set of data. 

### Changing the Number of Relevant Documents Retrieved
The number of retrieved documents is controlled by the `SIMILAR_DOCUMENTS_LIMIT` variable in the `config.toml` file. By default, the top 10 relevant documents are retrieved when you prompt the model. You can raise or lower the number of retrieved relevant documents by changing the `SIMILAR_DOCUMENTS_LIMIT` variable. Be careful to not set it to high since as the number of similar documents retrieved increases so does the computational complexity of response generation. 

To reflect this change, you will have to rebuild and restart the application with the following commands in the terminal: 
```
docker compose down 
docker compose up --build 
```

## Tl;dr Running Instructions 
Clone the repo: `git clone https://github.com/jdavis-uah/alet-cybercamp.git`

Assuming you have installed Docker Desktop, you can run the following commands to lauch the application. 
- `docker compose up -d --build`
- `docker exec ollama ollama pull gemma3:1b`
    - This will download the Gemma3 open source Gemini model 
- `docker exec ollama ollama pull gemma3:latest`
    - This will download the larger Gemma3 open source Gemini model 
- `docker exec ollama ollama pull tinyllama`
    - This will download a smaller model you can experiment with 
- `docker compose down`
- `docker compose up` 
- Navigate to `http://localhost:8501` in your browser
- Upload a CSV file and begin having a conversation with your document 


## Known Issues 
1. In the terminal, the url directs you to http://0.0.0.0:8501. This is verified to work on Mac OSX. For Windows, I have seen it generate errors. If the site doesn't load, use the following URL: http://localhost:8501. 
2. I have seen issues where the system does not have enough memory to run the Gemma3:latest model. In fact, the Mac used to run the workshop could not run the code using the larger Gemma model. If your chat engine times out and you receive an error message about system memory, use a smaller model: `gemma3:1b` or `tinyllama`. 
3. If the application runs extremely slow, it is likely due to the number of documents used for retrieval or the size of the CSV file.
    1. If the application's chat engine takes an extremely long time to open up, it's likely the size of the CSV file being used. You can either use a smaller CSV file, or limit the number of rows loaded by the application. To limit the number of rows, open the `config.toml` file and change the `PROCESSING_ROW_LIMIT` variable from `-1` (load all rows) to a reasonable number. 
    2. If the application's chat engine is taking an extremely long time to generate a response, it is likely one of two things: the model used or the number of similar documents being loaded. You can experiment with changing both of these in the `config.toml` file as well. To change the model used to the smallest model, change the `LLM_MODEL_NAME` in `config.toml` to `tinyllama`. To change the number of similar documents loaded during a query (see the [description of RAG](#note-about-retrieval-augmented-generation)), change the `SIMILAR_DOCUMENTS_LIMIT` from `10` to a much lower value. 

**NOTE: If you change any of these values, you will need to stop the application and restart it.**
To stop the application and restart it, run the following commands from the terminal: 
```
docker compose down 
docker compose up 
```