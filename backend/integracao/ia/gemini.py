"""
Adaptador para a API do Google Gemini.

Usa o método generateContent, pedindo a resposta em JSON (responseMimeType).
O esquema não é enviado ao Gemini, porque ele aceita só um subconjunto do
JSON Schema; o formato vai descrito nas instruções, e a validação completa é
feita depois, em dominio/roteirizacao.py.

Atenção: no plano gratuito, o Google pode usar os prompts para treinar seus
modelos. Os prompts do TripScripter não levam dados pessoais do usuário —
só destino, datas, ritmo e interesses.

Documentação: https://ai.google.dev/api/generate-content
"""

from .base import ClienteIA, ErroNoServicoDeIA, enviar_json, ler_json_gerado
from .prompt import INSTRUCOES_DO_SISTEMA, montar_pedido_ao_usuario

ENDERECO_DA_API = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


class ClienteGemini(ClienteIA):
    nome = "Gemini"

    def __init__(self, chave_api, modelo, tempo_limite):
        if not chave_api:
            raise ErroNoServicoDeIA("a chave GEMINI_API_KEY não foi configurada no .env")
        self.chave_api = chave_api
        self.modelo = modelo
        self.tempo_limite = tempo_limite

    def montar_corpo(self, pedido):
        return {
            "systemInstruction": {"parts": [{"text": INSTRUCOES_DO_SISTEMA}]},
            "contents": [{"role": "user", "parts": [{"text": montar_pedido_ao_usuario(pedido)}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.6},
        }

    def sugerir_roteiro(self, pedido):
        resposta = enviar_json(
            ENDERECO_DA_API.format(modelo=self.modelo),
            # A chave vai no cabeçalho, e não na URL, para não aparecer em logs.
            {"x-goog-api-key": self.chave_api},
            self.montar_corpo(pedido),
            self.tempo_limite,
        )
        try:
            partes = resposta["candidates"][0]["content"]["parts"]
            texto = "".join(parte.get("text", "") for parte in partes)
        except (KeyError, IndexError, TypeError) as erro:
            raise ErroNoServicoDeIA("resposta do Gemini fora do formato esperado") from erro
        return ler_json_gerado(texto)
