import io
import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, mock_open, patch

dotenv_module = types.ModuleType("dotenv")
dotenv_module.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv_module)

membrane_module = types.ModuleType("membrane")
sys.modules.setdefault("membrane", membrane_module)

import main


class MainModuleTests(unittest.IsolatedAsyncioTestCase):
    async def test_setup_hook_loads_all_python_cogs_and_syncs_tree(self):
        fake_client = SimpleNamespace(
            load_extension=AsyncMock(),
            tree=SimpleNamespace(sync=AsyncMock()),
        )

        with patch("main.os.listdir", return_value=["about.py", "ping.py", "README.md"]):
            await main.Client.setup_hook(fake_client)

        fake_client.load_extension.assert_has_awaits(
            [call("cogs.about"), call("cogs.ping")]
        )
        fake_client.tree.sync.assert_awaited_once()


class MainRuntimeTests(unittest.TestCase):
    def test_handler_returns_memory_summary(self):
        handler = SimpleNamespace(
            send_response=MagicMock(),
            end_headers=MagicMock(),
            wfile=io.BytesIO(),
        )

        with patch("builtins.open", mock_open(read_data='{"summary": "hello world"}')):
            main.Handler.do_GET(handler)

        handler.send_response.assert_called_once_with(200)
        handler.end_headers.assert_called_once_with()
        self.assertEqual(handler.wfile.getvalue(), b"hello world")

    def test_main_starts_server_thread_and_runs_client(self):
        fake_client = MagicMock()
        fake_thread = MagicMock()

        with patch.dict(os.environ, {"DISCORD_TOKEN": "token"}, clear=False):
            with patch("main.Client", return_value=fake_client):
                with patch("main.threading.Thread", return_value=fake_thread) as thread_cls:
                    main.main()

        thread_cls.assert_called_once_with(target=main.run_server, daemon=True)
        fake_thread.start.assert_called_once_with()
        fake_client.run.assert_called_once_with("token")
