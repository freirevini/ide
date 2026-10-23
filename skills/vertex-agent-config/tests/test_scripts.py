"""Testes mínimos dos scripts. Rodar: python -m pytest tests/ -q  (ou python -m unittest)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_config as gc  # noqa: E402
import inspecionar_agentes as ia  # noqa: E402


class TestTabelaDeModelos(unittest.TestCase):
    def test_modelos_espelham_referencia(self):
        doc = (RAIZ / "references" / "modelos.md").read_text(encoding="utf-8")
        for mid in gc.MODELOS:
            self.assertIn(f"`{mid}`", doc, f"{mid} está em MODELOS mas não em modelos.md")

    def test_defaults_por_modelo(self):
        self.assertEqual(gc.MODELOS["gemini-3.8-flash"].default_nivel, "MEDIUM")
        self.assertEqual(gc.MODELOS["gemini-4-argon"].default_nivel, "MEDIUM")
        self.assertEqual(gc.MODELOS["gemini-3.1-pro-preview"].default_nivel, "HIGH")
        self.assertEqual(gc.MODELOS["gemini-3.5-flash-lite"].default_nivel, "MINIMAL")

    def test_minimal_so_onde_existe(self):
        for mid in ("gemini-4-argon", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.1-pro-preview"):
            self.assertNotIn("MINIMAL", gc.MODELOS[mid].niveis, mid)
        for mid in ("gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"):
            self.assertIn("MINIMAL", gc.MODELOS[mid].niveis, mid)

    def test_desconhecido_nunca_minimal(self):
        for mid in ("gemini-3.9-flash", "gemini-4.1-pro", "gemini-5-x", "gemini-4-neon"):
            m, avisos = gc.resolver_modelo(mid)
            self.assertNotIn("MINIMAL", m.niveis, mid)
            self.assertEqual(m.estagio, "inferido", mid)
            self.assertTrue(avisos, mid)

    def test_alias_pro_sem_preview(self):
        m, avisos = gc.resolver_modelo("gemini-3.1-pro")
        self.assertEqual(m.estagio, "preview")
        self.assertTrue(any("gemini-3.1-pro-preview" in a for a in avisos))

    def test_2_5_retirado(self):
        m, avisos = gc.resolver_modelo("gemini-2.5-flash")
        self.assertEqual(m.estagio, "retirado")
        linhas, _, avisos2 = gc.montar("classificacao", "gemini-2.5-flash")
        self.assertEqual(linhas, [])
        self.assertTrue(avisos2)


class TestGerarConfig(unittest.TestCase):
    def cfg(self, perfil, modelo):
        linhas, notas, avisos = gc.montar(perfil, modelo)
        return "\n".join(linhas), "\n".join(notas), "\n".join(avisos)

    def test_flash_sem_amostragem_e_sem_top_p(self):
        cfg, _, _ = self.cfg("classificacao", "gemini-3.8-flash")
        self.assertNotIn("top_p=", cfg)
        self.assertNotIn("temperature=", cfg)
        self.assertIn('thinking_level="MEDIUM"', cfg)
        self.assertIn("default deste modelo: MEDIUM", cfg)

    def test_temperature_so_onde_funciona(self):
        cfg, _, _ = self.cfg("avaliacao-regras", "gemini-3.1-pro-preview")
        self.assertIn("temperature=1.0", cfg)
        self.assertNotIn("top_p=", cfg)

    def test_seed_so_confirmado(self):
        cfg, _, _ = self.cfg("alto-risco", "gemini-4-argon")
        self.assertNotIn("seed=42", cfg)
        cfg, _, _ = self.cfg("alto-risco", "gemini-3.1-pro-preview")
        self.assertIn("seed=42", cfg)

    def test_argon_janela_unificada(self):
        cfg, _, _ = self.cfg("documento-longo", "gemini-4-argon")
        self.assertIn("janela unificada", cfg)

    def test_minimal_nunca_emitido_em_3_8_argon_e_desconhecido(self):
        for mid in ("gemini-3.8-flash", "gemini-4-argon", "gemini-3.9-flash"):
            cfg, _, _ = self.cfg("triagem", mid)
            self.assertNotIn('thinking_level="MINIMAL"', cfg, mid)

    def test_nano_banana_rejeita_amostragem(self):
        cfg, notas, _ = self.cfg("imagem", "gemini-nano-banana-2.1")
        self.assertNotIn("seed=", cfg)
        self.assertIn("erro", notas.lower())

    def test_preview_e_depreciado_avisam(self):
        _, _, avisos = self.cfg("avaliacao-regras", "gemini-3.1-pro-preview")
        self.assertIn("PREVIEW", avisos)
        _, _, avisos = self.cfg("classificacao", "gemini-3.7-flash")
        self.assertIn("depreciado", avisos)


class TestInspecionarAgentes(unittest.TestCase):
    def test_env_ids_novos_e_migracao(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / ".env").write_text("GEMINI_MODEL=gemini-2.5-flash\n", encoding="utf-8")
            (raiz / "app.py").write_text(
                'IMG = "gemini-nano-banana-2.1"\n'
                'PRO = "gemini-3.1-pro"\n'
                'FLASH = "gemini-3.8-flash"\n'
                'cfg = dict(temperature=0.0)\n',
                encoding="utf-8",
            )
            rel = ia.varrer(raiz)
            pend = ia.pendencias(rel)
            trechos = [h["trecho"] for h in rel["achados"]["model_id"]]
            self.assertTrue(any("nano-banana-2.1" in t for t in trechos))
            self.assertTrue(any("GEMINI_MODEL=gemini-2.5-flash" in t for t in trechos), ".env não varrido")
            self.assertTrue(any("gemini-2.5" in p for p in pend))
            self.assertTrue(any("gemini-3.1-pro sem -preview" in p for p in pend))
            self.assertTrue(any(p.startswith("MIGRAÇÃO") for p in pend))

    def test_pro_preview_nao_e_legado(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "app.py").write_text('PRO = "gemini-3.1-pro-preview"\n', encoding="utf-8")
            pend = ia.pendencias(ia.varrer(raiz))
            self.assertFalse(any("sem -preview" in p for p in pend))


if __name__ == "__main__":
    unittest.main()
