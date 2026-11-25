"""
Clientes de inteligência artificial (padrão Adapter, ADR 003).

    ClienteIA            interface: o que qualquer provedor precisa oferecer
    ├── ClienteGroq      adaptador para a API do Groq
    ├── ClienteGemini    adaptador para a API do Google Gemini
    └── ClienteIASimulado  roteiro montado sem internet, para demonstração e reserva

O provedor em uso é escolhido no .env (IA_PROVEDOR) e montado por fabrica.py.
Trocar de provedor não exige alterar nenhuma outra parte do sistema.
"""

from .base import ClienteIA, ErroNoServicoDeIA, PedidoDeRoteiro

__all__ = ["ClienteIA", "ErroNoServicoDeIA", "PedidoDeRoteiro"]
