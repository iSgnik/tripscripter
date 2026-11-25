"""
Camada de integração (Figura 3 do Documento de Arquitetura).

Encapsula o consumo dos serviços externos atrás de interfaces próprias,
conforme o ADR 003 (padrão Adapter). Nenhuma outra camada conhece o provedor
concreto: elas usam apenas a interface.

- ia/: interface ClienteIA e os adaptadores Groq, Gemini e simulado.

ClienteMapas e ClienteClima, também previstos no ADR 003, ainda não foram
implementados.
"""
