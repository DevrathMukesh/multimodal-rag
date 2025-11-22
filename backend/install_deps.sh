#!/bin/bash
# Install dependencies workflow for conda rag environment
# Usage: ./install_deps.sh [package_name]

set -e

CONDA_ENV="rag"
REQUIREMENTS_FILE="requirements.txt"

# Activate conda environment
echo "🔧 Activating conda environment: $CONDA_ENV"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $CONDA_ENV

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    # No package specified, install all from requirements.txt
    echo "📦 Installing all dependencies from $REQUIREMENTS_FILE..."
    pip install -r $REQUIREMENTS_FILE
    echo "✅ All dependencies installed!"
else
    # Package specified, add to requirements.txt first, then install
    PACKAGE="$1"
    echo "➕ Adding $PACKAGE to $REQUIREMENTS_FILE..."
    
    # Check if package already exists in requirements.txt
    if grep -q "^${PACKAGE}" $REQUIREMENTS_FILE; then
        echo "⚠️  $PACKAGE already exists in $REQUIREMENTS_FILE"
    else
        echo "$PACKAGE" >> $REQUIREMENTS_FILE
        echo "✅ Added $PACKAGE to $REQUIREMENTS_FILE"
    fi
    
    echo "📦 Installing $PACKAGE..."
    pip install "$PACKAGE"
    echo "✅ $PACKAGE installed!"
fi

echo ""
echo "🧪 Testing critical imports..."
python -c "from langchain_google_genai import ChatGoogleGenerativeAI; from langchain_ollama import OllamaEmbeddings; print('✓ All critical imports work!')" || echo "❌ Import test failed"

