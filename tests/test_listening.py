import importlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock


fake_ai = types.ModuleType("ai.ai")


async def generate_response(*args, **kwargs):
    return None


async def annoying_response(*args, **kwargs):
    return None


fake_ai.generate_response = generate_response
fake_ai.annoying_response = annoying_response
sys.modules["ai.ai"] = fake_ai

listening_module = importlib.import_module("cogs.listening")
Listen = listening_module.Listen


class FakeTyping:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeChannel:
    def __init__(self, channel_id, name, history_messages):
        self.id = channel_id
        self.name = name
        self._history_messages = history_messages
        self.send = AsyncMock()

    def history(self, limit=10):
        async def iterator():
            for message in self._history_messages[:limit]:
                yield message

        return iterator()

    def typing(self):
        return FakeTyping()


def make_history_message(content, author_name, author_id, is_bot=False):
    return SimpleNamespace(
        content=content,
        author=SimpleNamespace(name=author_name, id=author_id, bot=is_bot),
    )


def make_interaction(channel_id, manage_channels):
    return SimpleNamespace(
        user=SimpleNamespace(
            guild_permissions=SimpleNamespace(manage_channels=manage_channels)
        ),
        channel=SimpleNamespace(id=channel_id, name="general"),
        response=SimpleNamespace(send_message=AsyncMock()),
    )


class ListenCogTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = SimpleNamespace(process_commands=AsyncMock())
        self.cog = Listen(self.bot)

    async def test_on_message_handles_ai_errors_without_crashing(self):
        async def boom(*args, **kwargs):
            raise RuntimeError("boom")

        channel = FakeChannel(
            channel_id=42,
            name="general",
            history_messages=[
                make_history_message("hey", "alice", 1),
                make_history_message("what's up", "bob", 2),
            ],
        )
        message = SimpleNamespace(
            content="hi kaelum",
            author=SimpleNamespace(id=99, name="carol", bot=False),
            channel=channel,
        )
        self.cog.listening_channels = {42: boom}

        await self.cog.on_message(message)

        channel.send.assert_awaited_once_with("AI ERROR: boom")
        self.bot.process_commands.assert_awaited_once_with(message)

    async def test_listen_requires_manage_channels_permission(self):
        interaction = make_interaction(channel_id=100, manage_channels=False)
        self.cog.listening_channels = {}

        await self.cog.listen.callback(self.cog, interaction)

        interaction.response.send_message.assert_awaited_once_with(
            "You need Manage Channels to do that.",
            ephemeral=True,
        )
        self.assertNotIn(100, self.cog.listening_channels)

    async def test_purge_requires_manage_channels_permission(self):
        interaction = make_interaction(channel_id=101, manage_channels=False)
        self.cog.listening_channels = {101: generate_response}

        await self.cog.purge.callback(self.cog, interaction)

        interaction.response.send_message.assert_awaited_once_with(
            "You need Manage Channels to do that.",
            ephemeral=True,
        )
        self.assertIn(101, self.cog.listening_channels)

    async def test_listen_adds_channel_for_authorized_user(self):
        interaction = make_interaction(channel_id=102, manage_channels=True)
        self.cog.listening_channels = {}

        await self.cog.listen.callback(self.cog, interaction)

        interaction.response.send_message.assert_awaited_once_with(
            "Began listening in #general.",
            ephemeral=True,
        )
        self.assertIs(self.cog.listening_channels[102], generate_response)
