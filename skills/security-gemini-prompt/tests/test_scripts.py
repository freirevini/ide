"""Testes mínimos dos scripts. Rodar: python -m pytest tests/ -q  (ou python -m unittest)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / "scripts"
sys.path.insert(0, str(SCRIPTS))

import auditar_prompt as ap  # noqa: E402
import red_team_local as rt  # noqa: E402
import validar_saida as vs  # noqa: E402

FONTE = "O produto custa R$ 18.500,00 e o prazo é de 30 dias.\nRodapé: oferta válida até 31/12.\n"
REGRAS = [{"id": "R1", "texto": "preço deve aparecer"}, {"id": "R2", "texto": "prazo obrigatório"}]


def _proj(tmp: str, nome: str, conteudo: str) -> Path:
    raiz = Path(tmp)
    (raiz / "app").mkdir(exist_ok=True)
    (raiz / "app" / nome).write_text(conteudo, encoding="utf-8")
    return raiz


class TestValidarDecisao(unittest.TestCase):
    def test_favoravel_com_evidencia_conforme_passa(self):
        r = vs.validar_decisao({"decisao": "aprovado", "evidencias": [
            {"regra_id": "R1", "trecho_citado": "custa R$ 18.500,00", "conforme": True}]}, REGRAS, FONTE)
        self.assertTrue(r.ok, r.incoerencias)
        self.assertEqual(r.detalhes["decisao_final"], "aprovado")

    def test_favoravel_sem_evidencia_reprova(self):
        r = vs.validar_decisao({"decisao": "aprovado", "evidencias": []}, REGRAS, FONTE)
        self.assertFalse(r.ok)
        self.assertEqual(r.detalhes["decisao_final"], "revisao_humana")

    def test_favoravel_com_contraria_valida_reprova(self):
        r = vs.validar_decisao({"decisao": "aprovado", "evidencias": [
            {"regra_id": "R2", "trecho_citado": "prazo é de 30 dias", "conforme": False}]}, REGRAS, FONTE)
        self.assertFalse(r.ok)
        self.assertEqual(r.detalhes["decisao_final"], "revisao_humana")

    def test_desfavoravel_com_contraria_passa(self):
        r = vs.validar_decisao({"decisao": "reprovado", "evidencias": [
            {"regra_id": "R2", "trecho_citado": "prazo  é de 30 dias", "conforme": False}]}, REGRAS, FONTE)
        self.assertTrue(r.ok, r.incoerencias)

    def test_sem_campo_conforme_nao_verificavel(self):
        r = vs.validar_decisao({"decisao": "aprovado", "evidencias": [
            {"regra_id": "R1", "trecho_citado": "custa R$ 18.500,00"}]}, REGRAS, FONTE)
        self.assertFalse(r.ok)
        self.assertTrue(any("conforme" in i for i in r.incoerencias))

    def test_violacoes_sao_contrarias(self):
        r = vs.validar_decisao({"decisao": "reprovado", "violacoes": [
            {"regra_id": "R2", "trecho_citado": "prazo é de 30 dias"}]}, REGRAS, FONTE)
        self.assertTrue(r.ok, r.incoerencias)

    def test_trecho_curto_nao_ancora(self):
        r = vs.validar_decisao({"decisao": "aprovado", "evidencias": [
            {"regra_id": "R1", "trecho_citado": "R$", "conforme": True}]}, REGRAS, FONTE)
        self.assertFalse(r.ok)
        self.assertEqual(r.detalhes["evidencias_favoraveis"], [])

    def test_trecho_fabricado(self):
        r = vs.validar_decisao({"decisao": "reprovado", "evidencias": [
            {"regra_id": "R2", "trecho_citado": "prazo é de 90 dias corridos", "conforme": False}]}, REGRAS, FONTE)
        self.assertFalse(r.ok)
        self.assertTrue(any("fabricada" in i for i in r.incoerencias))

    def test_truncamento(self):
        r = vs.validar_decisao({"decisao": "revisao_humana", "evidencias": []}, REGRAS, FONTE,
                               finish_reason="MAX_TOKENS")
        self.assertFalse(r.ok)

    def test_manipulacao_bloqueia_favoravel(self):
        r = vs.validar_decisao({"decisao": "aprovado", "evidencias": [
            {"regra_id": "R1", "trecho_citado": "custa R$ 18.500,00", "conforme": True}]},
            REGRAS, FONTE, manipulacao_detectada=True)
        self.assertEqual(r.detalhes["decisao_final"], "revisao_humana")


class TestValidarExtracaoCitacoes(unittest.TestCase):
    def test_extracao_fabricado_e_numeros(self):
        r = vs.validar_extracao({"prazo": "90 dias", "total": 18500}, FONTE)
        self.assertIn("prazo", r.detalhes["campos_fabricados"])
        r2 = vs.validar_extracao({"total": 18500}, FONTE, numeros=True)
        self.assertTrue(r2.ok, r2.incoerencias)
        r3 = vs.validar_extracao({"total": 18500}, FONTE, ignorar=("total",))
        self.assertTrue(r3.ok)

    def test_citacoes(self):
        r = vs.validar_citacoes(["prazo é de 30 dias", "oferta válida até 31/13"], FONTE)
        self.assertEqual(r.detalhes["citacoes_fabricadas"], ["oferta válida até 31/13"])


class TestAuditar(unittest.TestCase):
    def codigos(self, rel):
        return {a["codigo"] for a in rel["achados"]}

    def test_sem_gemini_nao_audita(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "calc.py", "def soma(a, b):\n    return a + b\n"))
            self.assertFalse(rel["gemini"])
            self.assertEqual(rel["achados"], [])

    def test_errors_ignore_nao_dispara_f04(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\ndef ler(p):\n    return open(p, errors="ignore").read()\n'))
            self.assertNotIn("F-04", self.codigos(rel))

    def test_regex_imperativa_dispara_f04(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\nimport re\nRX = re.compile(r"ignore|aprove|desconsidere", re.I)\n'))
            self.assertIn("F-04", self.codigos(rel))

    def test_f22_so_com_temperature(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'MODEL="gemini-3.8-flash"\ncfg=dict(thinking_level="LOW")\n'))
            self.assertNotIn("F-22", self.codigos(rel))
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'MODEL="gemini-3.8-flash"\ncfg=dict(temperature=0.0)\n'))
            self.assertIn("F-22", self.codigos(rel))

    def test_f05_nao_dispara_com_system_instruction(self):
        src = ('from google.genai import types\nINSTRUCOES = "Avalie."\n'
               'def montar(t):\n    return f"<documento_nao_confiavel>\\n{t}\\n</documento_nao_confiavel>\\nFim do conteúdo não confiável."\n'
               'def avaliar(c, t):\n    return c.models.generate_content(model="gemini-3.1-pro-preview", contents=[montar(t)],\n'
               '        config=types.GenerateContentConfig(system_instruction=INSTRUCOES))\n')
        with tempfile.TemporaryDirectory() as d:
            self.assertNotIn("F-05", self.codigos(ap.auditar(_proj(d, "a.py", src))))

    def test_f05_dispara_na_mesma_string(self):
        src = ('from google import genai\n'
               'def montar(t, regras):\n    return f"<documento_nao_confiavel>\\n{t}\\n</documento_nao_confiavel>\\nRegras aplicáveis: {regras}"\n')
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("F-05", self.codigos(ap.auditar(_proj(d, "a.py", src))))

    def test_f23_contexto_vai_para_verificar(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\nparts=[types.Part(file_data=f, media_resolution="low")]\n'))
            self.assertNotIn("F-23", self.codigos(rel))
            self.assertTrue(any(v["codigo"] == "F-23" for v in rel["verificar"]))

    def test_f11_so_com_rag(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\n'))
            self.assertNotIn("F-11", self.codigos(rel))
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\nstore = VectorStore(); store.ingest(docs)\n'))
            self.assertIn("F-11", self.codigos(rel))

    def test_json_loads_nao_conta_como_validacao(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\nout = json.loads(resp.text)\n'))
            self.assertTrue(any(v["codigo"] == "F-02" for v in rel["verificar"]))
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\nout = validar_decisao(resp.parsed, regras, texto)\n'))
            self.assertFalse(any(v["codigo"] == "F-02" for v in rel["verificar"]))

    def test_ausentes_vao_para_verificar_sem_severidade(self):
        with tempfile.TemporaryDirectory() as d:
            rel = ap.auditar(_proj(d, "a.py", 'from google import genai\n'))
            self.assertTrue(rel["verificar"])
            self.assertTrue(all(v["severidade"] is None for v in rel["verificar"]))
            self.assertFalse(any(a["codigo"] in ("F-01", "F-02", "F-03") for a in rel["achados"]))


class TestRedTeam(unittest.TestCase):
    def test_oraculo_detecta_tudo(self):
        res = rt.testar(rt.detector_de_referencia, rt.DOCUMENTO_BASE)
        self.assertTrue(all(r["detectado"] for r in res))
        self.assertEqual(set(rt.taxas(res)), set(rt.FAMILIAS))

    def test_detector_importado_da_raiz_e_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "dets.py").write_text(
                'import re\nRX = re.compile(r"ignore|disregard", re.I)\n'
                'def imperativo(t): return bool(RX.search(t))\n'
                'def nada(t): return False\n', encoding="utf-8")
            base = raiz / "baseline.json"
            cmd = [sys.executable, str(SCRIPTS / "red_team_local.py"), "testar",
                   "--detector", "dets:imperativo", "--raiz", str(raiz), "--baseline", str(base)]
            p1 = subprocess.run(cmd, capture_output=True, text=True, cwd=RAIZ)
            self.assertEqual(p1.returncode, 0, p1.stderr)
            self.assertTrue(base.exists())
            self.assertIn("controle", json.loads(base.read_text()))
            p2 = subprocess.run(cmd, capture_output=True, text=True, cwd=RAIZ)
            self.assertEqual(p2.returncode, 0, p2.stderr)
            cmd_pior = cmd[:cmd.index("dets:imperativo")] + ["dets:nada"] + cmd[cmd.index("dets:imperativo") + 1:]
            p3 = subprocess.run(cmd_pior, capture_output=True, text=True, cwd=RAIZ)
            self.assertEqual(p3.returncode, 1)
            self.assertIn("REGRESSÃO", p3.stderr)


if __name__ == "__main__":
    unittest.main()
