#!/bin/bash
clear

enable_virual_env () {

    source ./venv/bin/activate
    command -v git > /dev/null 2 >&1
    if [ $? -eq 0 ]; 
        then
          echo "Repo status: " && git pull
    else
        echo "Git isn't installed/added to path"
    fi
    echo "-----------------------------"
    pip install -r requirements.txt --quiet --exists-action i
    python3.10 main.py
    
}

if [ -d ./venv/bin ] 
    then
        echo "Detected an existing Virtual Environment"
        enable_virual_env
else
    echo "Creating a new Virtual Environment"
    if command -v python3 > /dev/null 2 >&1 && python3 --version | grep -q 3.10
    
        then
            echo "Detected Python 3.10"
            python3.10 -m pip list | grep -q virtualenv
            clear
        if [ $? -eq 0 ]
            then
                echo "Detected virtualenv module"
                python3.10 -m venv venv
                enable_virual_env
        else
            echo "Installing virtualenv module"
            python3.10 -m pip install virtualenv
            enable_virual_env
        fi
    else
        echo "Exiting: Python 3.10 is not installed"
        exit 1
    fi
fi
