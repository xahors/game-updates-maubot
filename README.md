# Плагин Game Updates для Maubot

Плагин Maubot, который отслеживает обновления игр и публикует патчноуты прямо в ваших Matrix-комнатах.

## Возможности

- Добавление игр по Steam App ID из ссылки магазина (например, `store.steampowered.com/app/<game_id>`).
- Бот проверяет обновления раз в час и отправляет последнее обновление для подписанных игр.
- Ответы бота на **русском или английском** — язык выбирается автоматически для каждой Matrix-комнаты (см. ниже).

## Команды

Все команды начинаются с префикса `!steam`.

- `!steam add <STEAM_APP_ID>` — подписать текущий канал на обновления указанной игры. Бот автоматически получит и покажет официальное название игры.
- `!steam remove <STEAM_APP_ID>` — отписать текущий канал от указанной игры.
- `!steam list` — список игр (названия и ID), за которыми следит канал.
- `!steam latest <STEAM_APP_ID>` — вручную получить и показать последние патчноуты или информацию об обновлении, не дожидаясь фонового цикла.
- `!steam pause` — приостановить или возобновить уведомления об обновлениях в текущем канале.

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

Периодичность: **10 с** задержка после старта, затем проверка **каждый час**; между играми в одном проходе пауза **10 с**.

## Язык ответов (RU / EN)

Переводятся **служебные тексты бота** (подтверждения команд, заголовки уведомлений, ссылки вроде «Читать патчноуты в Steam»). Если комната отвечает на **русском**, заголовок и текст патчноута с Steam (если они не на русском) автоматически переводятся перед публикацией.

### Когда бот отвечает по-русски

Для комнаты выбирается русский, если выполняется **любое** из условий:

1. **Кириллица в сообщениях комнаты** — бот обрабатывает обычные Matrix-сообщения (не только команды). Если в тексте есть кириллица, комната помечается в БД (`room_settings.language = ru`) и дальше ответы в этой комнате идут на русском, пока настройка сохранена.
2. **Кириллица в контексте команды** — текст самой команды, название игры из Steam или заголовок новости об обновлении содержат кириллицу (например, локализованное название игры).
3. **Комната уже помечена как русскоязычная** — после любого русскоязычного сообщения в канале последующие команды на латинице (`!steam add 123`) тоже получают русские ответы.

### Когда остаётся английский

- Команды только из латиницы и цифр, **английское** название игры, в комнате ещё **не было** сообщений с кириллицей.
- Пример: `!steam add 4753960` для *Meow Squad: Incremental Fishing* → ответ на английском, пока канал не «узнан» как русскоязычный.

### Особенности

| Ситуация | Поведение |
|----------|-----------|
| Первое сообщение в комнате — русское в чате | Комната запоминает RU; команды и hourly-уведомления — на русском |
| Только английские команды, без русского чата | Ответы на английском |
| Игра с кириллицей в названии | RU для этой операции; название может помочь выбрать RU |
| `!steam pause` и др. | Тот же выбор языка, что и для `add` / `list` |
| Сброс на EN вручную | **Нет** отдельной команды сброса; язык комнаты не переключается обратно автоматически |

Чтобы «включить» русский в канале с английскими командами, достаточно **одного** обычного сообщения на русском в той же комнате (до или после подписки на игры).

## Сборка

1. **Рекомендуется:** в каталоге с `maubot.yaml` выполните [`mbc build`](https://docs.mau.fi/maubot/usage/cli/build.html). Для разработки: `mbc build -u` — сборка и загрузка на сервер maubot.
2. **Удобный вариант:** `.\build.ps1` (Windows) или `./build.sh` (Linux/macOS) — читают `id` и `version` из `maubot.yaml` и создают файл вида `build/NEXT.game-updates-v1.0.0.mbp`.

В архив `.mbp` попадают только `maubot.yaml` и `bot.py`.

## Установка

1. Соберите плагин (см. раздел «Сборка») или упакуйте файлы вручную в архив `.mbp`.
2. Загрузите собранный `.mbp` из каталога `build/` (например, `build/NEXT.game-updates-v1.0.0.mbp`) в веб-интерфейсе Maubot.
3. Создайте клиента и экземпляр, свяжите их и пригласите бота в нужную Matrix-комнату.

## Обновление

Новую версию можно поставить **поверх** уже установленной: в `maubot.yaml` должен остаться тот же `id` (`NEXT.game-updates`), а поле `version` — быть выше предыдущей. Клиента Matrix и экземпляр плагина пересоздавать не нужно.

1. Соберите новый `.mbp` (см. раздел «Сборка») или выполните `mbc build -u`, если CLI настроен на ваш сервер Maubot.
2. Загрузите архив в веб-интерфейсе Maubot (раздел плагинов). Пакет с тем же `id` **заменит** старую версию плагина.
3. **Перезагрузите экземпляр** (`instance`), к которому привязан бот (кнопка reload/restart в UI или `mbc reload <instance-id>`). Пока экземпляр не перезапущен, может работать старый код в памяти, даже если новый `.mbp` уже загружен.
4. При старте Maubot сам применит недостающие миграции БД (если они появились в новой версии).

**Сохраняется:** подписки на игры, пауза уведомлений, язык комнаты (`room_settings`) и записи о последних известных обновлениях.

**Обычно не требуется:** удалять плагин перед загрузкой, заново создавать клиента или instance (кроме случая, когда вы меняете `id` плагина).

После обновления при необходимости проверьте работу командой `!steam latest <STEAM_APP_ID>` и при ошибках посмотрите логи экземпляра Maubot.

---

## English

# Game Updates Maubot Plugin

A Maubot plugin that tracks backend game updates and posts patch notes directly into your Matrix rooms.

## Features

- Add games by Steam game ID from the Steam store link (e.g. `store.steampowered.com/app/<game_id>`).
- The bot checks for game updates hourly and posts the latest update for subscribed games.
- Bot replies in **Russian or English** — locale is chosen automatically per Matrix room (see below).

## Commands

All commands are prefixed with `!steam`.

- `!steam add <STEAM_APP_ID>` - Subscribes the current channel to updates for the specified game. The bot will automatically fetch and confirm the game's official name.
- `!steam remove <STEAM_APP_ID>` - Unsubscribes the current channel from the specified game.
- `!steam list` - Displays a list of all games (with their names and IDs) currently being tracked in the channel.
- `!steam latest <STEAM_APP_ID>` - Manually fetches and displays the latest patch notes or update info for a specific game instantly, without waiting for the background loop.
- `!steam pause` - Toggles pausing/resuming update notifications for the current channel.

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

Schedule: **10 s** delay after startup, then checks **every hour**; **10 s** pause between games in each run.

## Response language (RU / EN)

The bot's **UI strings** are translated (command confirmations, notification headings, links like “Read patch notes on Steam”). When a room uses **Russian**, patch note **titles and bodies** from Steam are translated to Russian before posting if they are not already in Russian.

### When the bot replies in Russian

Russian is used for a room if **any** of these apply:

1. **Cyrillic in room messages** — the bot listens to normal Matrix messages, not only commands. Cyrillic text sets `room_settings.language = ru` in the database; later replies in that room stay Russian while that setting persists.
2. **Cyrillic in command context** — the command text, the Steam game name, or the update headline contains Cyrillic (e.g. a localized title).
3. **Room already marked Russian** — after any Russian message in the channel, even all-Latin commands (`!steam add 123`) get Russian replies.

### When English is used

- Commands are Latin-only, the **game name is English**, and the room has **no** Cyrillic messages yet.
- Example: `!steam add 4753960` for *Meow Squad: Incremental Fishing* → English reply until the channel is recognized as Russian.

### Notes

| Situation | Behavior |
|-----------|----------|
| First Russian chat message in the room | Room remembered as RU; commands and hourly alerts use Russian |
| English-only commands, no Russian chat | English replies |
| Game with Cyrillic in the name | RU for that interaction; name can tip locale to RU |
| `!steam pause`, etc. | Same locale rules as `add` / `list` |
| Manual reset to EN | **No** dedicated command; room language does not auto-revert |

To get Russian replies in a channel that only uses English commands, send **one** normal Russian message in that room (before or after subscribing).

## Building

1. **Recommended:** run [`mbc build`](https://docs.mau.fi/maubot/usage/cli/build.html) in the directory that contains `maubot.yaml`. For development, use `mbc build -u` to build and upload to your maubot server.
2. **Convenient:** run `.\build.ps1` on Windows or `./build.sh` on Linux/macOS — they read `id` and `version` from `maubot.yaml` and produce a file like `build/NEXT.game-updates-v1.0.0.mbp`.

The `.mbp` archive includes only `maubot.yaml` and `bot.py`.

## Installation

1. Build the plugin (see **Building**) or zip the plugin files into an `.mbp` archive manually.
2. Upload the built `.mbp` from the `build/` directory (e.g. `build/NEXT.game-updates-v1.0.0.mbp`) to your Maubot manager via the web interface.
3. Create a new client and instance, link them, and invite the bot to your desired Matrix room.

## Updating

You can install a newer release **on top of** an existing one: keep the same plugin `id` in `maubot.yaml` (`NEXT.game-updates`) and bump `version`. You do not need to recreate the Matrix client or plugin instance.

1. Build a new `.mbp` (see **Building**) or run `mbc build -u` if your Maubot CLI is configured for your server.
2. Upload the archive in the Maubot web UI (Plugins). A package with the same `id` **replaces** the previous plugin version.
3. **Reload the plugin instance** tied to your bot (reload/restart in the UI, or `mbc reload <instance-id>`). Until the instance restarts, the old code may still be running in memory even after the new `.mbp` is uploaded.
4. On startup, Maubot applies any new database migrations shipped with the plugin.

**Preserved:** game subscriptions, notification pause state, per-room language (`room_settings`), and last-known update IDs.

**Usually unnecessary:** uninstalling the plugin before upload, or recreating the client/instance (unless you change the plugin `id`).

After upgrading, verify with `!steam latest <STEAM_APP_ID>` if needed, and check the Maubot instance logs on errors.
