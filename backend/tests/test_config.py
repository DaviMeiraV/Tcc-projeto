"""Testes para os padrões de configuração por ambiente."""

import os
import unittest
from unittest.mock import patch

from app.core.config import Settings


class SettingsTest(unittest.TestCase):
    def test_url_local_fora_do_render(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.ANALISE_API_URL, "http://127.0.0.1:8001")

    def test_url_de_producao_no_render(self):
        with patch.dict(os.environ, {"RENDER": "true"}, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(
            settings.ANALISE_API_URL,
            "https://opencv-bodyposture-api.onrender.com",
        )

    def test_variavel_de_ambiente_pode_sobrescrever_url(self):
        url_personalizada = "https://api-postural.example.com"
        with patch.dict(
            os.environ,
            {"RENDER": "true", "ANALISE_API_URL": url_personalizada},
            clear=True,
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.ANALISE_API_URL, url_personalizada)


if __name__ == "__main__":
    unittest.main()
