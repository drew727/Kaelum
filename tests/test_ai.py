import importlib
import json
import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock


class FakeAsyncFile:
    def __init__(self, storage, path, mode):
        self.storage = storage
        self.path = path
        self.mode = mode

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def read(self):
        return self.storage[self.path]

    async def write(self, data):
        self.storage[self.path] = data
        return len(data)


class FakeAiofilesModule(types.ModuleType):
    def __init__(self):
        super().__init__("aiofiles")
        self.storage = {}

    def open(self, path, mode="r"):
        return FakeAsyncFile(self.storage, path, mode)


def stub_ai_dependencies():
    sys.modules.pop("ai.ai", None)
    os.environ["LLMKEY"] = "test-llm"
    os.environ["GEMINI_API_KEY"] = "test-gemini"

    fake_aiofiles = FakeAiofilesModule()

    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda: None

    openai_module = types.ModuleType("openai")

    class DummyAsyncOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    openai_module.AsyncOpenAI = DummyAsyncOpenAI

    google_module = types.ModuleType("google")
    genai_module = types.ModuleType("google.genai")
    genai_types_module = types.ModuleType("google.genai.types")

    class DummyGenaiClient:
        def __init__(self, *args, **kwargs):
            pass

    class DummyTool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyGoogleSearch:
        pass

    class DummyGenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    genai_module.Client = DummyGenaiClient
    genai_types_module.Tool = DummyTool
    genai_types_module.GoogleSearch = DummyGoogleSearch
    genai_types_module.GenerateContentConfig = DummyGenerateContentConfig
    genai_module.types = genai_types_module
    google_module.genai = genai_module

    membrane_module = types.ModuleType("membrane")

    class DummyMembraneClient:
        def __init__(self, *args, **kwargs):
            pass

    class DummySensitivity:
        pass

    class DummyTrustContext:
        pass

    class DummyMemoryType:
        pass

    membrane_module.MembraneClient = DummyMembraneClient
    membrane_module.Sensitivity = DummySensitivity
    membrane_module.TrustContext = DummyTrustContext
    membrane_module.MemoryType = DummyMemoryType

    requests_module = types.ModuleType("requests")
    bs4_module = types.ModuleType("bs4")
    bs4_module.BeautifulSoup = object
    numpy_module = types.ModuleType("numpy")

    sys.modules["aiofiles"] = fake_aiofiles
    sys.modules["dotenv"] = dotenv_module
    sys.modules["openai"] = openai_module
    sys.modules["google"] = google_module
    sys.modules["google.genai"] = genai_module
    sys.modules["google.genai.types"] = genai_types_module
    sys.modules["membrane"] = membrane_module
    sys.modules["requests"] = requests_module
    sys.modules["bs4"] = bs4_module
    sys.modules["numpy"] = numpy_module

    module = importlib.import_module("ai.ai")
    return module, fake_aiofiles


def groq_response(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


def gemini_text_response(text):
    return SimpleNamespace(text=text)


class AiModuleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module, self.fake_aiofiles = stub_ai_dependencies()
        self.module.file_path = "memory.json"
        self.fake_aiofiles.storage[self.module.file_path] = json.dumps({"summary": "old"})
        self.module.groq_queue = ["groq-a"]
        self.module.gemini_queue = ["gem-a"]

    async def test_generate_response_returns_none_when_filter_says_no(self):
        self.module.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(
                        side_effect=[
                            groq_response("NO"),
                            groq_response("new summary"),
                        ]
                    )
                )
            )
        )
        self.module.gemini_client = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(generate_content=AsyncMock())
            )
        )

        result = await self.module.generate_response("alice: hi", "alice: hi")

        self.assertIsNone(result)
        self.assertEqual(
            json.loads(self.fake_aiofiles.storage[self.module.file_path])["summary"],
            "new summary",
        )
        self.module.gemini_client.aio.models.generate_content.assert_not_awaited()

    async def test_generate_response_falls_back_to_groq_when_gemini_fails(self):
        self.module.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(
                        side_effect=[
                            groq_response("YES"),
                            groq_response("updated memory"),
                            groq_response("groq fallback reply"),
                        ]
                    )
                )
            )
        )
        self.module.gemini_client = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(
                    generate_content=AsyncMock(side_effect=Exception("gemini down"))
                )
            )
        )

        result = await self.module.generate_response("alice: hi", "bob: hey")

        self.assertEqual(result, "groq fallback reply")
        self.assertEqual(
            json.loads(self.fake_aiofiles.storage[self.module.file_path])["summary"],
            "updated memory",
        )

    async def test_annoying_response_uses_gemini_when_available(self):
        self.module.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=AsyncMock())
            )
        )
        self.module.gemini_client = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(
                    generate_content=AsyncMock(
                        return_value=gemini_text_response("annoying gemini")
                    )
                )
            )
        )

        result = await self.module.annoying_response("ctx", "recent")

        self.assertEqual(result, "annoying gemini")
        self.module.client.chat.completions.create.assert_not_awaited()

    async def test_annoying_response_falls_back_to_groq(self):
        self.module.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(return_value=groq_response("annoying groq"))
                )
            )
        )
        self.module.gemini_client = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(
                    generate_content=AsyncMock(side_effect=Exception("gemini down"))
                )
            )
        )

        result = await self.module.annoying_response("ctx", "recent")

        self.assertEqual(result, "annoying groq")
