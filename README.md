# Berlin Termin Bot

A [Selenium](https://www.selenium.dev/) bot for obtaining an appointment at the Burgeramt in Berlin.

I did not want to open source this as this makes it harder for the people without IT knowledge to obtain an appointment, but as there are already people who make a benefit of this (50 euro per appointment!) I thought it would be a good thing to make the tools available to everyone. This project is therefore a counter measurement against those people as well as the inability of the Ausländerbehörde to provide sufficient appointments.

Take a look at the video [Hinter verschlossenen Türen – Mysterium Ausländerbehörde - ZDF Magazin Royale
](https://www.youtube.com/watch?v=s7HrAGlni50) to find out more about the bad shape of this agency.

## Pre-requisites
* Python 3.6+ : `brew install python3`
* pip3 : `brew install pip3`

## Setup

* Telegram bot creation: 
  * Find telegram bot named "@botfarther", he will help you with creating and managing your bot.
  * Print “/help” and you will see all possible commands that the botfather can operate.
  * To create a new bot type “/newbot” or click on it.
  * Congratulations! You've just created your Telegram bot. You will see a new API token generated for it.
  * To get CHAT_ID 
    * ```curl https://api.telegram.org/bot<API_TOKEN>/getUpdates```
* Update env variables in `auslanderbehorde_bot.sh`:
  * `export TELEGRAM_API_TOKEN=<TELEGRAM_API_TOKEN>`
  * `export TELEGRAM_CHAT_ID=<TELEGRAM_CHAT_ID>`
* `git clone https://github.com/amalrajvinoth/berlin-termin-bot.git`
* Setup a virtualenv via `virtualenv venv` and activate it
* Install dependencies via `pip3 install -r requirements.txt`
* Put a `chromedriver` binary from <https://chromedriver.chromium.org/downloads> into the directory
* Configure `auslanderbehorde_bot.py` or `berlin_bot.py` according to your needs (see below)
* Start the bot via `auslanderbehorde_bot.sh` or `berlin_bot.sh`

## Configuration and Support

I do not give any kind of support and/or advice on how to configure this bot as I wrote this for a friend of mine and thankfully she was able to get an appointment with this bot.
You can read the [selenium docs](https://selenium-python.readthedocs.io/locating-elements.html#) and adjust `auslanderbehorde_bot.py` or `berlin_bot.py` in order to configure it according to your needs.

## Thanks

I would like to express our sincere gratitude to the original creator of this project:

- [capital-G](https://github.com/capital-G/berlin-auslanderbehorde-termin-bot)

## License

AGPL-3.0
