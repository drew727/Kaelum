import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from cogs.about import About, setup as setup_about
from cogs.ping import Ping, setup as setup_ping


class CogCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_about_command_sends_embed(self):
        cog = About(bot=object())
        interaction = SimpleNamespace(
            response=SimpleNamespace(send_message=AsyncMock())
        )

        await cog.about.callback(cog, interaction)

        interaction.response.send_message.assert_awaited_once()
        embed = interaction.response.send_message.await_args.kwargs["embed"]
        self.assertEqual(embed.title, "About this bot!")
        self.assertIn("conversationally fluent bot", embed.description.lower())

    async def test_ping_command_sends_healthcheck_message(self):
        cog = Ping(bot=object())
        interaction = SimpleNamespace(
            response=SimpleNamespace(send_message=AsyncMock())
        )

        await cog.spawn.callback(cog, interaction)

        interaction.response.send_message.assert_awaited_once_with("I'm here!")

    async def test_about_setup_adds_cog(self):
        client = SimpleNamespace(add_cog=AsyncMock())

        await setup_about(client)

        client.add_cog.assert_awaited_once()
        self.assertIsInstance(client.add_cog.await_args.args[0], About)

    async def test_ping_setup_adds_cog(self):
        client = SimpleNamespace(add_cog=AsyncMock())

        await setup_ping(client)

        client.add_cog.assert_awaited_once()
        self.assertIsInstance(client.add_cog.await_args.args[0], Ping)
