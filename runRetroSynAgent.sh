#!/bin/bash

python main.py --material Polyimide --num_results 10 --alignment True --expansion True --filtration False

uvicorn vistree:app --reload
