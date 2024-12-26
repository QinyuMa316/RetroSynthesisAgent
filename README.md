# RetroSynthesisAgent
code for "Leveraging Large Language Models as Knowledge-Driven Agents for Reliable Retrosynthesis Planning" paper
## Requirements

```
pip install rdkit requests python-dotenv PyMuPDF scholarly openai networkx graphviz pubchempy Pillow fastapi pydantic uvicorn pyvis loguru
```

## Data
eMolecules download URL: https://downloads.emolecules.com/free/2024-07-01/
Download it and turn it to a set as a format of json
## `env.` File Setting
+ Set your OpenAI API key (`API_KEY`) and optional `BASE_URL` to use the LLM.
+ Set the `HEADERS` and `COOKIES` from your browser for web scraping of literatures.

## Run the demo
`sh exeRroSynAgent.sh`

Parameter Description:
`--material`: Specifies the material to be processed.
`--num_results`: Defines the number of PDF to be processed.
`--filtration`: Determines whether to apply filtration to the reactions.

[![Watch Demo](assets/thumbnail.png)](assets/demo-video.mp4)
