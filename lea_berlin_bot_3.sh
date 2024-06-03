#!/bin/bash
export PATH=$PATH:~/work/other/berlin-termin-bot
export COLOREDLOGS_LEVEL_STYLES='spam=22;debug=28;verbose=34;notice=220;warning=202;success=118,bold;error=124;critical=background=red'
source ./venv/bin/activate
LEA_CATEGORY="Aufenthaltstitel in einen neuen Pass übertragen" \
LEA_SUB_CATEGORY="" \
LEA_VISA_TYPE="Übertragen einer Aufenthaltserlaubnis auf einen neuen Pass" \
python3 lea_berlin_bot.py
