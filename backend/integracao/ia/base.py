"""A interface ClienteIA e os tipos que ela recebe e devolve."""

import json
import socket
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


class ErroNoServicoDeIA(Exception):
    """O provedor não respondeu, recusou a chamada ou devolveu algo ilegível."""


@dataclass
class PedidoDeRoteiro:
    """Tudo o que a IA precisa saber para sugerir o roteiro de uma viagem."""

    destino: str
    datas: list[date]
    estilo: str | None
    atividades_por_dia: int
    # Pares (categoria, nível de 1 a 5), do maior interesse para o menor.
    preferencias: list[tuple[str, int]] = field(default_factory=list)

    @property
    def total_de_dias(self):
        return len(self.datas)


class ClienteIA(ABC):
    """
    Interface que todo provedor de IA implementa (ClienteIA, Figura 2).

    sugerir_roteiro devolve um dicionário no formato de prompt.ESQUEMA_DO_ROTEIRO.
    A resposta não é considerada confiável: quem chama valida cada campo
    (dominio/roteirizacao.py) antes de gravar qualquer coisa no banco.
    """

    #: Nome exibido ao usuário e registrado na resposta da API.
    nome = "desconhecido"

    @abstractmethod
    def sugerir_roteiro(self, pedido: PedidoDeRoteiro) -> dict:
        """Devolve a sugestão de roteiro ou lança ErroNoServicoDeIA."""


def enviar_json(url, cabecalhos, corpo, tempo_limite):
    """
    Envia uma requisição POST com corpo JSON e devolve a resposta já decodificada.

    Usa apenas a biblioteca padrão do Python, para não acrescentar dependências.
    Qualquer falha de rede, de tempo ou de formato vira ErroNoServicoDeIA, com
    uma mensagem que pode ser registrada sem expor a chave de API.
    """
        requisicao = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TripScripter/1.0",
            **cabecalhos,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=tempo_limite) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        # 401: chave inválida · 429: cota esgotada · 5xx: falha do provedor
        raise ErroNoServicoDeIA(f"o provedor respondeu com o código HTTP {erro.code}") from erro
    except (urllib.error.URLError, socket.timeout, TimeoutError) as erro:
        raise ErroNoServicoDeIA("sem resposta do provedor (rede indisponível ou tempo esgotado)") from erro
    except json.JSONDecodeError as erro:
        raise ErroNoServicoDeIA("o provedor devolveu uma resposta que não é JSON") from erro


def ler_json_gerado(texto):
    """Converte em dicionário o texto JSON que o modelo escreveu."""
    try:
        dados = json.loads(texto)
    except (TypeError, json.JSONDecodeError) as erro:
        raise ErroNoServicoDeIA("o modelo não devolveu um JSON válido") from erro
    if not isinstance(dados, dict):
        raise ErroNoServicoDeIA("o modelo devolveu JSON fora do formato esperado")
    return dados
