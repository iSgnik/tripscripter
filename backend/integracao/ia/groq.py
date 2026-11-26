"""
Adaptador para a API do Groq.

A API do Groq segue o formato da API da OpenAI (chat completions). O pedido
de saída estruturada usa o JSON Schema de prompt.py em modo "best-effort"
(strict = false): o modelo tenta seguir o formato, e a validação completa é
feita depois, em dominio/roteirizacao.py.

Documentação: https://console.groq.com/docs/structured-outputs
"""

from .base import ClienteIA, ErroNoServicoDeIA, enviar_json, ler_json_gerado
from .prompt import ESQUEMA_DO_ROTEIRO, INSTRUCOES_DO_SISTEMA, montar_pedido_ao_usuario

ENDERECO_DA_API = "https://api.groq.com/openai/v1/chat/completions"


class ClienteGroq(ClienteIA):
    nome = "Groq"

    def __init__(self, chave_api, modelo, tempo_limite):
        if not chave_api:
            raise ErroNoServicoDeIA("a chave GROQ_API_KEY não foi configurada no .env")
        self.chave_api = chave_api
        self.modelo = modelo
        self.tempo_limite = tempo_limite

    def montar_corpo(self, pedido):
        return {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": INSTRUCOES_DO_SISTEMA},
                {"role": "user", "content": montar_pedido_ao_usuario(pedido)},
            ],
            "temperature": 0.6,
            "max_completion_tokens": 6000,
            "reasoning_effort": "low",
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "roteiro", "strict": False, "schema": ESQUEMA_DO_ROTEIRO},
            },
        }

    def sugerir_roteiro(self, pedido):
        resposta = enviar_json(
            ENDERECO_DA_API,
            {"Authorization": f"Bearer {self.chave_api}"},
            self.montar_corpo(pedido),
            self.tempo_limite,
        )
        try:
            texto = resposta["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as erro:
            raise ErroNoServicoDeIA("resposta do Groq fora do formato esperado") from erro
        return ler_json_gerado(texto)
