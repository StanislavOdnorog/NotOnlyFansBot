#!/bin/bash

source venv/bin/activate

nohup python src/bot.py >> .bot_log
nohup python src/bot.py -s >> .suport_log
nohup python src/bot.py -u >> .update_log

ps -fe | grep bot.py
