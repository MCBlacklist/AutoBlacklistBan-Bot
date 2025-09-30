# Discord Blacklist/Unblacklist Bot

A Discord bot that automatically prompts a ban for any blacklisted user, enhancing server security and moderation efficiency.

## Features

* **Automatic Blacklist Detection:** Monitors incoming users and cross-references them against a blacklist.
* **Instant Ban Prompt:** Automatically prompts a ban for any blacklisted user upon detection.
* **Customizable Responses:** Allows customization of ban messages and reasons.
* **Easy Configuration:** Simple setup with environment variables for seamless integration.

## Installation

### Prerequisites

* Python 3.8 or higher
* `pip` (Python package installer)

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/MCBlacklist/AutoBlacklistBan-Bot.git
   cd AutoBlacklistBan-Bot
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**

   Copy the example environment file and edit it with your bot's token and other necessary details.

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file to include your bot's token and any other required information.

4. **Run the Bot:**

   ```bash
   python main.py
   ```

   Your bot should now be running and monitoring for blacklisted users.

## Usage

Once the bot is running, it will automatically monitor incoming users and check them against the blacklist. If a match is found, the bot will prompt a ban for that user.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/MCBlacklist/AutoBlacklistBan-Bot/blob/master/LICENSE) file for details.

---

