#!/bin/bash
export PATH=$PATH:~/work/other/berlin-termin-bot
export COLOREDLOGS_LEVEL_STYLES='spam=22;debug=28;verbose=34;notice=220;warning=202;success=118,bold;error=background=red;critical=background=red'
export COLOREDLOGS_LOG_FORMAT='%(asctime)s,%(msecs)03d APT %(levelname)s %(message)s'
python3 apartment_berlin_bot.py
