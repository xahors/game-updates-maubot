import asyncio
import logging
from typing import Dict, List

import aiohttp
from maubot import Plugin, MessageEvent
from maubot.handlers import command
from mautrix.types import TextMessageEventContent, Format, MessageType
from mautrix.util.async_db import UpgradeTable, Scheme

upgrade_table = UpgradeTable()

@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn, scheme: Scheme) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS game_subscriptions (
            room_id TEXT,
            app_id TEXT,
            PRIMARY KEY (room_id, app_id)
        )
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS room_settings (
            room_id TEXT PRIMARY KEY,
            paused BOOLEAN DEFAULT FALSE
        )
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS last_updates (
            app_id TEXT PRIMARY KEY,
            last_update_id TEXT
        )
        """
    )

class GameUpdatesBot(Plugin):
    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable:
        return upgrade_table

    async def start(self) -> None:
        self.check_task = asyncio.create_task(self.check_updates_loop())

    async def stop(self) -> None:
        self.check_task.cancel()

    @command.new("game-updates", require_subcommand=True)
    async def game_updates(self, evt: MessageEvent) -> None:
        """Manage game update subscriptions for this channel."""
        pass

    @game_updates.subcommand("pause")
    async def pause(self, evt: MessageEvent) -> None:
        """Pause or resume game update notifications in this channel."""
        room_id = str(evt.room_id)
        
        row = await self.database.fetchrow("SELECT paused FROM room_settings WHERE room_id=$1", room_id)
        current = row["paused"] if row else False
        new_status = not current
        
        if row is None:
            await self.database.execute("INSERT INTO room_settings (room_id, paused) VALUES ($1, $2)", room_id, new_status)
        else:
            await self.database.execute("UPDATE room_settings SET paused=$1 WHERE room_id=$2", new_status, room_id)
            
        status = "paused" if new_status else "resumed"
        await evt.respond(f"Game updates {status} for this channel.")

    @game_updates.subcommand("add")
    @command.argument("app_id", pass_raw=True)
    async def add_game(self, evt: MessageEvent, app_id: str) -> None:
        """Subscribe this channel to updates for a specific Steam App ID."""
        app_id = app_id.strip()
        if not app_id:
            await evt.respond("Please provide a Steam App ID. Usage: !game-updates add <ID>")
            return
        
        game_info = await self.fetch_game_info(app_id)
        if not game_info:
            await evt.respond(f"Could not retrieve info for Steam App ID {app_id}. Please check if the ID is valid.")
            return

        room_id = str(evt.room_id)
        
        row = await self.database.fetchrow("SELECT app_id FROM game_subscriptions WHERE room_id=$1 AND app_id=$2", room_id, app_id)
        if row:
            await evt.respond(f"{game_info['name']} (App ID {app_id}) is already in the list for this channel.")
            return

        await self.database.execute("INSERT INTO game_subscriptions (room_id, app_id) VALUES ($1, $2)", room_id, app_id)
        
        content = TextMessageEventContent(
            msgtype=MessageType.NOTICE,
            format=Format.HTML,
            body=f"Added {game_info['name']} (App ID {app_id}) to updates list for this channel.",
            formatted_body=(
                f"✅ Added <b>{game_info['name']}</b> (App ID {app_id}) to the updates list for this channel."
            )
        )
        await evt.respond(content)

    @game_updates.subcommand("remove")
    @command.argument("app_id", pass_raw=True)
    async def remove_game(self, evt: MessageEvent, app_id: str) -> None:
        """Unsubscribe this channel from a specific Steam App ID."""
        app_id = app_id.strip()
        room_id = str(evt.room_id)
        
        row = await self.database.fetchrow("SELECT app_id FROM game_subscriptions WHERE room_id=$1 AND app_id=$2", room_id, app_id)
        if row:
            game_info = await self.fetch_game_info(app_id)
            game_name = game_info['name'] if game_info else f"App ID {app_id}"
            
            await self.database.execute("DELETE FROM game_subscriptions WHERE room_id=$1 AND app_id=$2", room_id, app_id)
            await evt.respond(f"Removed {game_name} from updates list for this channel.")
        else:
            await evt.respond(f"App ID {app_id} not found in this channel's list.")

    @game_updates.subcommand("list")
    async def list_games(self, evt: MessageEvent) -> None:
        """List all games this channel is currently subscribed to."""
        room_id = str(evt.room_id)
        rows = await self.database.fetch("SELECT app_id FROM game_subscriptions WHERE room_id=$1", room_id)
        
        if not rows:
            await evt.respond("Not subscribed to any games in this channel.")
            return

        game_list_messages = []
        for row in rows:
            app_id = row["app_id"]
            game_info = await self.fetch_game_info(app_id)
            game_name = game_info['name'] if game_info else f"Unknown Game (App ID {app_id})"
            game_list_messages.append(f"- {game_name} (App ID {app_id})")
        
        response_body = "Currently subscribed to the following games:\n" + "\n".join(game_list_messages)
        await evt.respond(response_body)

    async def fetch_game_info(self, app_id: str):
        url = f"https://api.steamcmd.net/v1/info/{app_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        app_data = data.get("data", {}).get(str(app_id), {})
                        game_name = app_data.get("common", {}).get("name")
                        if game_name:
                            return {"name": game_name}
        except Exception as e:
            self.log.warning(f"Error fetching game info for {app_id}: {e}")
        return None

    def _bbcode_to_html(self, text: str) -> str:
        """Convert Steam BBCode to simple HTML for Matrix."""
        if not text:
            return ""
            
        # Replace Steam's internal image variables with the actual CDN URL
        text = text.replace("{STEAM_CLAN_IMAGE}", "https://clan.cloudflare.steamstatic.com/images")
        
        # Basic replacements
        replacements = {
            "[b]": "<b>", "[/b]": "</b>",
            "[i]": "<i>", "[/i]": "</i>",
            "[u]": "<u>", "[/u]": "</u>",
            "[p]": "<p>", "[/p]": "</p>",
            "[list]": "<ul>", "[/list]": "</ul>",
            "[*]": "<li>", "[/*]": "</li>",
            "\\[": "[", "\\]": "]", # Unescape brackets
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        import re
        # Handle URLs: [url=http://...]text[/url]
        text = re.sub(r'\[url=(.+?)\](.*?)\[/url\]', r'<a href="\1">\2</a>', text)
        
        # Element and many Matrix clients block external images in message bodies for privacy/security.
        # Remove Steam's [img] and [img src="..."] tags entirely from the patch notes content.
        text = re.sub(r'\[img\s+src="(.*?)"\]\[/img\]', '', text)
        text = re.sub(r'\[img\](.*?)\[/img\]', '', text)
        
        # Limit length to avoid massive messages
        if len(text) > 2000:
            text = text[:1997] + "..."
            
        return text

    async def fetch_latest_update(self, app_id: str):
        # We use the official Steam News API to get actual patch notes
        url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={app_id}&count=10"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        newsitems = data.get("appnews", {}).get("newsitems", [])
                        
                        for item in newsitems:
                            tags = item.get("tags", [])
                            # Look for official patch notes or community announcements
                            if "patchnotes" in tags or item.get("feedname") == "steam_community_announcements":
                                game_info = await self.fetch_game_info(app_id)
                                game_name = game_info['name'] if game_info else f"App {app_id}"
                                
                                raw_contents = item.get("contents", "No patch notes provided.")
                                html_contents = self._bbcode_to_html(raw_contents)
                                
                                return {
                                    "title": item.get("title", "New Update"),
                                    "url": item.get("url"),
                                    "id": item.get("gid"),
                                    "name": game_name,
                                    "contents": html_contents,
                                    "date": item.get("date")
                                }
        except Exception as e:
            self.log.warning(f"Error fetching from steam news api for {app_id}: {e}")
            
        return None

    async def check_updates_loop(self):
        await asyncio.sleep(10) # Initial startup delay
        while True:
            try:
                # Fetch all subscriptions
                subs = await self.database.fetch("SELECT room_id, app_id FROM game_subscriptions")
                
                # Fetch settings
                paused_rows = await self.database.fetch("SELECT room_id, paused FROM room_settings")
                paused_rooms = {row["room_id"]: row["paused"] for row in paused_rows}

                # Fetch last updates
                last_updates_rows = await self.database.fetch("SELECT app_id, last_update_id FROM last_updates")
                last_updates = {row["app_id"]: row["last_update_id"] for row in last_updates_rows}
                
                # Group by room
                room_games = {}
                for row in subs:
                    room_id = row["room_id"]
                    if room_id not in room_games:
                        room_games[room_id] = []
                    room_games[room_id].append(row["app_id"])

                for room_id, app_ids in room_games.items():
                    if paused_rooms.get(room_id, False):
                        continue
                    
                    for app_id in app_ids:
                        update = await self.fetch_latest_update(app_id)
                        if update:
                            update_id = update["id"]
                            last_id = last_updates.get(app_id)
                            
                            if last_id != update_id:
                                is_first_check = app_id not in last_updates
                                
                                # Update database
                                if is_first_check:
                                    await self.database.execute("INSERT INTO last_updates (app_id, last_update_id) VALUES ($1, $2)", app_id, update_id)
                                else:
                                    await self.database.execute("UPDATE last_updates SET last_update_id=$1 WHERE app_id=$2", update_id, app_id)
                                last_updates[app_id] = update_id
                                
                                if not is_first_check:
                                    content = TextMessageEventContent(
                                        msgtype=MessageType.NOTICE,
                                        format=Format.HTML,
                                        body=f"New update for {update['name']}: {update['title']}\n{update['url']}",
                                        formatted_body=(
                                            f"🎮 <b>New Update for {update['name']}</b>: {update['title']}<br/><br/>"
                                            f"{update['contents']}<br/><br/>"
                                            f"<a href='{update['url']}'>Read full patch notes on Steam</a>"
                                        )
                                    )
                                    await self.client.send_message(room_id, content)
                        
                        await asyncio.sleep(10) # Gentle to the server
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log.error(f"Error in check loop: {e}")
            
            await asyncio.sleep(3600) # Check for updates once every hour

    @game_updates.subcommand("latest")
    @command.argument("app_id", pass_raw=True)
    async def latest_update(self, evt: MessageEvent, app_id: str) -> None:
        """Fetch and display the latest patch notes for a specific Steam App ID."""
        app_id = app_id.strip()
        if not app_id:
            await evt.respond("Please provide a Steam App ID. Usage: !game-updates latest <ID>")
            return
            
        update = await self.fetch_latest_update(app_id)
        if update:
            content = TextMessageEventContent(
                msgtype=MessageType.NOTICE,
                format=Format.HTML,
                body=f"Latest update for {update['name']}: {update['title']}\n{update['url']}",
                formatted_body=(
                    f"🎮 <b>Latest Update for {update['name']}</b>: {update['title']}<br/><br/>"
                    f"{update['contents']}<br/><br/>"
                    f"<a href='{update['url']}'>Read full patch notes on Steam</a>"
                )
            )
            await evt.respond(content)
        else:
            await evt.respond(f"Could not retrieve patch notes for Steam App ID {app_id}. It might be invalid or have no recent official announcements.")