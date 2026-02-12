#!/bin/bash
cd "$(dirname "$0")"
streamlit run src/app.py "$@"
