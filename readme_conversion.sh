#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
fi

if ! command -v md2tex &> /dev/null; then
    echo "ERROR: 'md2tex' not found."
    exit 1
fi

mkdir -p readme

md2tex README.md -c -o ./readme/README.tex -d article -u -f

# Step 2: Compile and Cleanup
if command -v pdflatex &> /dev/null; then
    echo "Compiling with pdflatex..."
    cd readme
    pdflatex -interaction=nonstopmode -shell-escape README.tex > /dev/null
    pdflatex -interaction=nonstopmode -shell-escape README.tex > /dev/null
    
    # Cleanup LaTeX garbage
    rm -f README.aux README.log README.out README.toc README.synctex.gz
    rm -rf _minted-README
    echo "Compilation and cleanup finished."
else
    echo "WARNING: 'pdflatex' not found. Skipping PDF generation."
fi


