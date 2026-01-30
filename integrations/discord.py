"""
Discord bot service for sending messages and handling interactions.
"""
import asyncio
from typing import Optional, Callable, Any
import discord
from discord import Webhook
import aiohttp

from config import DISCORD_BOT_TOKEN, DISCORD_WEBHOOK_URL, DISCORD_CHANNEL_ID


class DiscordService:
    """Service for Discord bot integration."""
    
    def __init__(self):
        """Initialize Discord service."""
        self.bot_token = DISCORD_BOT_TOKEN
        self.webhook_url = DISCORD_WEBHOOK_URL
        self.channel_id = DISCORD_CHANNEL_ID
        self.client: Optional[discord.Client] = None
        self.message_handler: Optional[Callable] = None
        
        # Determine which method to use
        if self.bot_token:
            self.mode = "bot"
        elif self.webhook_url:
            self.mode = "webhook"
        else:
            self.mode = None
            print("Warning: No Discord bot token or webhook URL configured")
    
    async def initialize_bot(self, message_handler: Optional[Callable] = None) -> None:
        """
        Initialize Discord bot client.
        
        Args:
            message_handler: Optional async function to handle incoming messages
                            Signature: async def handler(message: discord.Message) -> None
        """
        if self.mode != "bot":
            print("Bot token not configured, skipping bot initialization")
            return
        
        self.message_handler = message_handler
        
        # Set up intents - message_content is required for reading message content
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read message content
        
        try:
            self.client = discord.Client(intents=intents)
        except Exception as e:
            if "privileged intents" in str(e).lower():
                print("\n" + "=" * 60)
                print("ERROR: Privileged Intents Not Enabled")
                print("=" * 60)
                print("\nTo fix this, you need to enable 'MESSAGE CONTENT INTENT' in Discord Developer Portal:")
                print("\n1. Go to: https://discord.com/developers/applications/")
                print("2. Select your bot application")
                print("3. Go to 'Bot' section in the left sidebar")
                print("4. Scroll down to 'Privileged Gateway Intents'")
                print("5. Enable 'MESSAGE CONTENT INTENT'")
                print("6. Save changes")
                print("7. Restart the Discord bot")
                print("\n" + "=" * 60)
            raise
        
        @self.client.event
        async def on_ready():
            print(f'\n{"="*60}')
            print(f'✅ Discord bot logged in as {self.client.user}')
            print(f'   Bot ID: {self.client.user.id}')
            print(f'   Guilds: {len(self.client.guilds)}')
            for guild in self.client.guilds:
                print(f'   - {guild.name} (ID: {guild.id})')
            print(f'{"="*60}\n')
            print(f'📡 Bot is ready to receive messages!')
            print(f'   Make sure the bot has permission to read messages in your server.\n')
            
            # Send hello message to default channel if configured
            if self.channel_id:
                try:
                    channel = self.client.get_channel(int(self.channel_id))
                    if channel:
                        await channel.send("👋 Hello! Cal is now online and ready to help with your tasks and reminders!")
                        print(f'✅ Sent hello message to #{channel.name}')
                except Exception as e:
                    print(f'⚠ Could not send hello message: {e}')
            else:
                # Try to send to first available text channel in first guild
                if self.client.guilds:
                    guild = self.client.guilds[0]
                    # Find first text channel the bot can send messages to
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages:
                            try:
                                await channel.send("👋 Hello! Cal is now online and ready to help with your tasks and reminders!")
                                print(f'✅ Sent hello message to #{channel.name} in {guild.name}')
                                break
                            except Exception as e:
                                print(f'⚠ Could not send hello message to #{channel.name}: {e}')
                                continue
        
        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == self.client.user:
                return

            if self.message_handler:
                try:
                    await self.message_handler(message)
                except Exception as e:
                    print(f"Error in message handler: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Start the bot
        await self.client.start(self.bot_token)
    
    async def send_message(self, content: str, channel_id: Optional[str] = None) -> bool:
        """
        Send a message to Discord.
        
        Args:
            content: Message content
            channel_id: Channel ID (uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if self.mode == "bot" and self.client:
            return await self._send_via_bot(content, channel_id)
        elif self.mode == "webhook":
            return await self._send_via_webhook(content)
        else:
            print("Discord not configured, cannot send message")
            return False
    
    async def _send_via_bot(self, content: str, channel_id: Optional[str] = None) -> bool:
        """
        Send message via Discord bot.
        
        Args:
            content: Message content
            channel_id: Channel ID
            
        Returns:
            True if successful
        """
        try:
            target_channel_id = channel_id or self.channel_id
            if not target_channel_id:
                print("No channel ID specified for Discord message")
                return False
            
            channel = self.client.get_channel(int(target_channel_id))
            if not channel:
                print(f"Channel {target_channel_id} not found")
                return False
            
            await channel.send(content)
            return True
        except Exception as e:
            print(f"Error sending Discord message via bot: {e}")
            return False
    
    async def _send_via_webhook(self, content: str) -> bool:
        """
        Send message via Discord webhook.
        
        Args:
            content: Message content
            
        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(self.webhook_url, session=session)
                await webhook.send(content)
            return True
        except Exception as e:
            print(f"Error sending Discord message via webhook: {e}")
            return False
    
    async def close(self) -> None:
        """Close Discord connection."""
        if self.client:
            await self.client.close()
    
    def format_message(self, title: str, content: str, **kwargs) -> str:
        """
        Format a message for Discord.
        
        Args:
            title: Message title
            content: Message content
            **kwargs: Additional formatting options
            
        Returns:
            Formatted message string
        """
        message = f"**{title}**\n\n{content}"
        
        if kwargs.get("footer"):
            message += f"\n\n_{kwargs['footer']}_"
        
        return message
    
    def format_reminder(self, task_title: str, task_time: str, description: Optional[str] = None) -> str:
        """
        Format a task reminder message.
        
        Args:
            task_title: Task title
            task_time: Task time
            description: Optional task description
            
        Returns:
            Formatted reminder message
        """
        message = f"🔔 **Reminder: {task_title}**\n"
        message += f"⏰ Time: {task_time}\n"
        
        if description:
            message += f"\n{description}"
        
        return message


# Global instance
_discord_service: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """
    Get the global Discord service instance.
    
    Returns:
        DiscordService instance
    """
    global _discord_service
    if _discord_service is None:
        _discord_service = DiscordService()
    return _discord_service

