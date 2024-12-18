#!/bin/bash

python main.py --material Polyimide --num_results 10

uvicorn vistree:app --reload
