#!/bin/bash

nohup python src/bot.py >> .bot_log &
nohup python src/bot.py -s >> .support_log &
nohup python src/bot.py -u >> .update_log &

sleep 1
ps -fe | grep bot.py
