#!/bin/bash
export PATH=$PATH:~/work/other/berlin-termin-bot
export COLOREDLOGS_LEVEL_STYLES='spam=22;debug=28;verbose=34;notice=220;warning=202;success=118,bold;error=124;critical=background=red'
source ./venv/bin/activate
LEA_CATEGORY="Aufenthaltstitel - verlängern" \
LEA_SUB_CATEGORY="Erwerbstätigkeit" \
LEA_VISA_TYPE="Aufenthaltserlaubnis für Fachkräfte mit akademischer Ausbildung (§ 18b)" \
python3 lea_berlin_bot.py
