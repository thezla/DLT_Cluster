#!/bin/sh

pipenv run python logger.py &
pipenv run python debugger.py &
pipenv run python chain.py &
pipenv run python manager.py -p 5000 &
pipenv run python manager.py -p 5100