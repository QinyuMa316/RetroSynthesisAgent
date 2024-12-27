#!/bin/bash

python main.py --material Polyimide --num_results 10 --filtration False --alignment False

uvicorn vistree:app --reload
