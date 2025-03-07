# amazon-deals-telegram-bot

Create a telegram bot that scrapes deals from the Italian Amazon page and sends them to a channel. Ideal for automating an Amazon Deals Telegram channel with referral links.

This software does not make use of the Amazon's Product Adverising APIs so you can use this before having a qualified Amazon Associates account and does not use Keepa's APIs.

## Table of Contents

- [amazon-deals-telegram-bot](#amazon-deals-telegram-bot)
  - [Table of Contents](#table-of-contents)
  - [General Information](#general-information)
  - [Setup](#setup)
  - [Usage](#usage)
    - [Server Deployment](#server-deployment)
  - [License](#license)

## General Information

This project has the goal of creating an automatic telegram bot that scrapes deals from the Italian Amazon page and sends them to a specific channel. Once started, it scrapes all the deals on the first page of the website with deals above 50%, taking all the IDs of the different products. It then selects one product that was not chosen recently and sends a message to the specified channel with the product image, its title, the link (which may also be an affiliate link), and a catchy phrase in Italian with the discount rate and the new price.
It can be used to automate the tedious job of selecting the deals from Amazon, although with a lower quality of selection, with the potential monetary benefit that can come from the Amazon affiliate program.

[Here](https://t.me/OfferteDiMimmo) is a working example of the telegram bot in action.

**ATTENTION:** this script is based on website scraping. For this reason, it may be possible that, with the passing of time, the change of layout in the product pages may lead to the impossibility of successfully retrieving product information, lowering the number of products that may be selected.

## Setup

- Install the required Python libraries specified in [requirements.txt](requirements.txt) with `pip install -r requirements.txt`.
- Install Chrome or Chromium
- Create your telegram bot:
    - Start the bot [@BotFather](https://telegram.me/BotFather)
    - Create your bot. Take note of the _bot token_ and the _bot username_
- Use the information of the newly created bot to set the variables in the [.env](.env.example) file (you need to rename the file _.env.example_ to _.env_ on your local machine). Make sure not to share the information contained in it

## Usage

To send a single message, just run the module with `python amazon-deals-telegram-bot`. The first time, it will take some time because it will download the correct version of the chromedriver and then retrieve all the possible IDs from which it may choose. This setup time will be lowered in successive runs because the chromedriver will be cached if the previously downloaded version is still up-to-date and present on your machine, and because the ids are saved in a file and updated only if more than 2 hours have passed since the last time they were retrieved.
It is possible to periodically send messages by setting up a cron job that runs the script.

### Server Deployment

To deploy this application to a server you can use a Selenium [grid](https://www.selenium.dev/documentation/grid/) with a node.
The easiest way to set it up is using the [Docker Compose file](docker-compose.yml) setting its specific additional environment variables to schedule executions.

## License

This source code is licensed by [Alberto Pasqualetto](https://github.com/albertopasqualetto) and [Lorenzo Asquini](https://github.com/lorenzo-asquini) (the authors) under the [MIT license](LICENSE).
