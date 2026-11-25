"""
Escolhe o cliente de IA conforme a configuração do .env.

    IA_PROVEDOR=groq | gemini | simulado     provedor principal
    IA_RESERVA=simulado | nenhuma            o que usar se o principal falhar

É o único ponto do sistema que conhece as classes concretas. O restante usa
apenas a interface ClienteIA.
"""

from django.conf import settings

from .base import ErroNoServicoDeIA
from .gemini import ClienteGemini
from .groq import ClienteGroq
from .simulado import ClienteIASimulado


def criar_cliente(provedor):
    """Devolve o cliente pedido. Lança ErroNoServicoDeIA se faltar a chave."""
    if provedor == "groq":
        return ClienteGroq(settings.GROQ_API_KEY, settings.GROQ_MODELO, settings.IA_TEMPO_LIMITE)
    if provedor == "gemini":
        return ClienteGemini(settings.GEMINI_API_KEY, settings.GEMINI_MODELO, settings.IA_TEMPO_LIMITE)
    if provedor == "simulado":
        return ClienteIASimulado()
    raise ErroNoServicoDeIA(f"provedor de IA desconhecido: {provedor!r}")


def criar_cliente_principal():
    return criar_cliente(settings.IA_PROVEDOR)


def criar_reserva():
    """Cliente usado quando o principal falha, ou None se não houver reserva."""
    return ClienteIASimulado() if settings.IA_RESERVA == "simulado" else None
