#!/bin/bash
export PATH=$PATH:~/work/other/berlin-termin-bot
export COLOREDLOGS_LEVEL_STYLES='spam=22;debug=28;verbose=34;notice=220;warning=202;success=118,bold;error=124;critical=background=red'
source ./venv/bin/activate
LEA_VISA_CATEGORY="Aufenthaltstitel - verlängern" \
LEA_VISA_SUB_CATEGORY="Familiäre Gründe" \
LEA_VISA_TYPE="Aufenthaltserlaubnis für Ehepartner, Eltern und Kinder von ausländischen Familienangehörigen (§§ 29-34)" \
python3 lea_berlin_bot.py
