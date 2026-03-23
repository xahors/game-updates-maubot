# Game Updates Maubot Plugin

A Maubot plugin that tracks backend game updates and posts patch notes directly into your Matrix rooms.

## Features

- Add games by steam game ID from steam store link (ex. store.steampowered.com/app/<game_id>.
- Bot checks for game updates hourly. Posts latest game update for subscribed games. 

## Commands

All commands are prefixed with `!game-updates`.

- `!game-updates add <STEAM_APP_ID>` - Subscribes the current channel to updates for the specified game. The bot will automatically fetch and confirm the game's official name.
- `!game-updates remove <STEAM_APP_ID>` - Unsubscribes the current channel from the specified game.
- `!game-updates list` - Displays a list of all games (with their names and IDs) currently being tracked in the channel.
- `!game-updates latest <STEAM_APP_ID>` - Manually fetches and displays the latest patch notes or update info for a specific game instantly, without waiting for the background loop.
- `!game-updates pause` - Toggles pausing/resuming update notifications for the current channel.

## How to find a Steam App ID

1. Go to the Steam store page for the game in your web browser.
2. Look at the URL in the address bar (e.g., `https://store.steampowered.com/app/2527500/MiSide/`).
3. The number right after `/app/` is the ID you need (in this case, `2527500`).

## How it works under the hood

The bot runs a background `asyncio` task (`check_updates_loop`) that wakes up once every hour. 

1. It queries its database for all subscribed games across all non-paused rooms.
2. It hits the Official Steam News API to check for new posts tagged with `patchnotes` or published in the `steam_community_announcements` feed.
3. If an update is found, it parses the BBCode to clean HTML (stripping out blocked external tracking images for Matrix compatibility).
4. If this update is newer than the one stored in the bot's database, it dispatches an HTML-formatted Matrix message alerting the room.

## Installation

1. Zip the plugin files into an `.mbp` archive
2. Upload the `game-updates.mbp` file to your Maubot manager via the web interface.
3. Create a new client and instance, link them, and invite the bot to your desired Matrix room.
