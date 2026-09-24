#!/usr/bin/env bash

# Resolve the absolute canonical path of the script directory, resolving symlinks
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

# Fallback directory if the script was copied (not symlinked) to a global bin directory
REPO_DIR="/home/superbypassudin/.clone/Github/ultimatevocalremovergui"

if [ ! -d "$SCRIPT_DIR/.venv" ] && [ -d "$REPO_DIR/.venv" ]; then
    SCRIPT_DIR="$REPO_DIR"
fi

cd "$SCRIPT_DIR" || exit 1

# Check if the virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment (.venv) not found in '$SCRIPT_DIR'."
    if [ -t 0 ]; then
        read -p "Would you like to run install_packages.sh now to set up the environment? [y/N]: " choice
        case "$choice" in
            [yY][eE][sS]|[yY])
                echo "Running install_packages.sh..."
                ./install_packages.sh || { echo "Installation failed."; exit 1; }
                ;;
            *)
                echo "Exiting. Please set up the environment before running Ultimate Vocal Remover."
                exit 1
                ;;
        esac
    else
        echo "Non-interactive terminal. Attempting to run install_packages.sh automatically..."
        ./install_packages.sh || { echo "Installation failed."; exit 1; }
    fi
fi

# Run the application using the python virtual environment interpreter
echo "Launching Ultimate Vocal Remover GUI..."
exec .venv/bin/python UVR.py "$@"
