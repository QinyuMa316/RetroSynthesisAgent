# RetroSynthesisAgent
**code for paper "Leveraging Large Language Models as Knowledge-Driven Agents for Reliable Retrosynthesis Planning".**

This project aims to conduct retrosynthesis planning for polymer materials based on literature, utilizing an LLM agent and knowledge graphs.

## Requirements
```
conda create -n retrosyn python=3.11
conda activate retrosyn
pip install rdkit requests python-dotenv PyMuPDF scholarly openai networkx graphviz pubchempy Pillow fastapi pydantic uvicorn pyvis loguru
```

## Data
+ eMolecules download URL: https://downloads.emolecules.com/free/
+ for this project, version: 2024-07-01
+ Download it and turn it to a set as a format of json

## `env.` File Setting
+ Set your OpenAI API key (`API_KEY`) and optional `BASE_URL` to use the LLM.
+ Set the `HEADERS` and `COOKIES` from your browser for web scraping of literatures in JSON
+ an example:
```
API_KEY=xxx
BASE_URL=xxx
HEADERS={"user-agent": "xxx"}
COOKIES={"xxx": "xxx", "xxx": "xxx"}
```

## Run the demo
```
sh runRetroSynAgent.sh
```

Parameter Description:
+ `--material`: Specifies the material to be processed.
+ `--num_results`: Defines the number of PDF to be processed.
+ `--alignment`: Determines whether to align entities.
+ `--expansion`: Determines whether to expand the tree with additional literature.
+ `--filtration`: Determines whether to apply filtration to the reactions.

We provide a demo video of its automated operation process:

[![Watch Demo](assets/thumbnail.png)](assets/demo-video.mp4)

+ After constructing the chemical retrosynthetic pathway tree for the target substance, a URL will be generated. You can open it directly in your local browser.
+ **When you hover over a node in the tree, the name of the substance represented by that node will be displayed.**
