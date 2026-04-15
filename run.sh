#!/bin/bash
export PATH="$PATH:/Users/iuseog/Library/Python/3.9/bin"
cd "$(dirname "$0")"
streamlit run app.py --server.port 8501
