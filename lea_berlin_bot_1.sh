#!/bin/bash
export PATH=$PATH:~/work/other/berlin-termin-bot
export COLOREDLOGS_LEVEL_STYLES='spam=22;debug=28;verbose=34;notice=220;warning=202;success=118,bold;error=124;critical=background=red'
export COLOREDLOGS_LOG_FORMAT='%(asctime)s,%(msecs)03d LEA %(levelname)s %(message)s'
LEA_FAMILY_REASON="Aufenthaltserlaubnis für Ehepartner, Eltern und Kinder von ausländischen Familienangehörigen (§§ 29-34)" LEA_FAMILY_REASON_CATEGORY="Familiäre Gründe" python3 lea_berlin_bot.py
