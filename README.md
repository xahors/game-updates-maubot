# Плагин Game Updates для Maubot

Плагин Maubot, который отслеживает обновления игр и публикует патчноуты прямо в ваших Matrix-комнатах.

## Возможности

- Добавление игр по Steam App ID из ссылки магазина (например, `store.steampowered.com/app/<game_id>`).
- Бот проверяет обновления раз в час и отправляет последнее обновление для подписанных игр.

## Команды

Все команды начинаются с префикса `!game-updates`.

- `!game-updates add <STEAM_APP_ID>` — подписать текущий канал на обновления указанной игры. Бот автоматически получит и покажет официальное название игры.
- `!game-updates remove <STEAM_APP_ID>` — отписать текущий канал от указанной игры.
- `!game-updates list` — список игр (названия и ID), за которыми следит канал.
- `!game-updates latest <STEAM_APP_ID>` — вручную получить и показать последние патчноуты или информацию об обновлении, не дожидаясь фонового цикла.
- `!game-updates pause` — приостановить или возобновить уведомления об обновлениях в текущем канале.

## Как узнать Steam App ID

1. Откройте страницу игры в магазине Steam в браузере.
2. Посмотрите URL в адресной строке (например, `https://store.steampowered.com/app/2527500/MiSide/`).
3. Число сразу после `/app/` — это нужный ID (в примере — `2527500`).

## Как это устроено

Бот запускает фоновую задачу `asyncio` (`check_updates_loop`), которая срабатывает раз в час.

1. Запрашивает из базы все подписанные игры во всех неприостановленных комнатах.
2. Обращается к официальному Steam News API за новыми постами с тегом `patchnotes` или из ленты `steam_community_announcements`.
3. При найденном обновлении парсит BBCode в чистый HTML (убирает внешние трекинг-картинки для совместимости с Matrix).
4. Если обновление новее сохранённого в базе, отправляет в комнату Matrix-сообщение в формате HTML.

## Сборка

1. **Рекомендуется:** в каталоге с `maubot.yaml` выполните [`mbc build`](https://docs.mau.fi/maubot/usage/cli/build.html). Для разработки: `mbc build -u` — сборка и загрузка на сервер maubot.
2. **Удобный вариант:** `.\build.ps1` (Windows) или `./build.sh` (Linux/macOS) — читают `id` и `version` из `maubot.yaml` и создают файл вида `NEXT.game-updates-v1.0.0.mbp`.

В архив `.mbp` попадают только `maubot.yaml` и `bot.py`.

## Установка

1. Соберите плагин (см. раздел «Сборка») или упакуйте файлы вручную в архив `.mbp`.
2. Загрузите собранный `.mbp` (например, `NEXT.game-updates-v1.0.0.mbp`) в веб-интерфейсе Maubot.
3. Создайте клиента и экземпляр, свяжите их и пригласите бота в нужную Matrix-комнату.

---

## English

# Game Updates Maubot Plugin

A Maubot plugin that tracks backend game updates and posts patch notes directly into your Matrix rooms.

## Features

- Add games by Steam game ID from the Steam store link (e.g. `store.steampowered.com/app/<game_id>`).
- The bot checks for game updates hourly and posts the latest update for subscribed games.

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

## Building

1. **Recommended:** run [`mbc build`](https://docs.mau.fi/maubot/usage/cli/build.html) in the directory that contains `maubot.yaml`. For development, use `mbc build -u` to build and upload to your maubot server.
2. **Convenient:** run `.\build.ps1` on Windows or `./build.sh` on Linux/macOS — they read `id` and `version` from `maubot.yaml` and produce a file like `NEXT.game-updates-v1.0.0.mbp`.

The `.mbp` archive includes only `maubot.yaml` and `bot.py`.

## Installation

1. Build the plugin (see **Building**) or zip the plugin files into an `.mbp` archive manually.
2. Upload the built `.mbp` file (e.g. `NEXT.game-updates-v1.0.0.mbp`) to your Maubot manager via the web interface.
3. Create a new client and instance, link them, and invite the bot to your desired Matrix room.
