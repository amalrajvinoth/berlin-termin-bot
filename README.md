# Berlin Termin Bot

A [Selenium](https://www.selenium.dev/) bot for obtaining an appointment at the `Ausländerbehörde` or `Bürgerämt` in Berlin.

Watch this video [Hinter verschlossenen Türen – Mysterium Ausländerbehörde - ZDF Magazin Royale
](https://www.youtube.com/watch?v=s7HrAGlni50) to understand more about the agency's issues.

## Pre-requisites
* Python 3.6+ : `brew install python3`
* pip3 : `brew install pip3`

## Setup

* Telegram bot creation:
  * Find telegram bot named `@botfather`, he will help you with creating and managing your bot. 
  * Print `/help` and you will see all possible commands that the `botfather` can operate. 
  * To create a new bot type `/newbot` or click on it. 
  * Congratulations! You've just created your Telegram bot. You will see a new API token generated for it.
* Clone this repository:
  * `git clone https://github.com/amalrajvinoth/berlin-termin-bot.git`
* To get telegram CHAT_ID created in Step 1, run the following command: 
  * ```curl https://api.telegram.org/bot<API_TOKEN>/getUpdates```
* Generate a `.env` file from sample file `.env.sample`
```dotenv
# LEA / Ausländerbehörde Configuration
LEA_NATIONALITY=Indien
LEA_NUMBER_OF_PERSON=drei Personen
LEA_LIVING_IN_BERLIN=Ja
LEA_NATIONALITY_OF_FAMILY_MEMBERS=Indien

# Telegram
TELEGRAM_API_TOKEN=<Your_Telegram_API_Token>
TELEGRAM_CHAT_ID=<Your_Telegram_Chat_ID>
```
* Setup a virtualenv via `sudo virtualenv venv` and activate it.
* Install dependencies via `sudo pip3 install -r requirements.txt`
* Put a latest version of `chromedriver` binary into this repository directory
  * downaload suitable chromedirver for your OS: https://googlechromelabs.github.io/chrome-for-testing/#stable
  * Add `chromedriver` to PATH: `echo 'export PATH=$PATH:<chromedriver_path>' > ~/.profile`

## Run
### LEA / Ausländerbehörde appointment
* Configure `lea_berlin_bot.py` according to your needs (see below)
* Start the bot via `lea_berlin_bot.sh`
  * `chmod +x lea_berlin_bot.sh`
  * `./lea_berlin_bot.sh`

### berlin Bürgerämt appointment
* Configure `apartment_berlin_bot.py` according to your needs (see below)
* Start the bot via `apartment_berlin_bot.sh`
  * `chmod +x apartment_berlin_bot.sh`
  * `./apartment_berlin_bot.sh`

### berlin Bürgerämt appointment
* Configure `apartment_berlin_bot.py` according to your needs (see below)
* Start the bot via `apartment_berlin_bot.sh`
  * `chmod +x apartment_berlin_bot.sh`
  * `./apartment_berlin_bot.sh`

## Configuration and Support

You can read the [selenium docs](https://selenium-python.readthedocs.io/locating-elements.html#) and adjust `auslanderbehorde_bot.py` or `berlin_bot.py` in order to configure it according to your needs.
By default, it looks appointment for `Residence permit for spouses parents and children of foreign family members (§§ 29-34)` for `3 person` from `India`. 
If you need different nationally and number of people adjust the configuration in `.env` file

## Thanks

I would like to express our sincere gratitude to the original creator of this project:

- [capital-G](https://github.com/capital-G/berlin-auslanderbehorde-termin-bot)

## License

AGPL-3.0
