"""
Montagem do prompt (montarPrompt, Figura 2) e formato esperado da resposta.

O mesmo prompt serve a todos os provedores. Cada adaptador só muda a forma de
enviá-lo, porque cada API tem seu próprio formato de requisição.
"""

# Mesmas categorias de dominio/regras.py. Repetidas aqui porque a camada de
# integração não depende do domínio (Figura 3); um teste garante que as duas
# listas continuem iguais.
CATEGORIAS = (
    "Cultura", "Gastronomia", "Arte", "Natureza", "História", "Compras", "Vida noturna", "Praia",
)

# Formato que a IA deve seguir, em JSON Schema. Os campos correspondem às
# colunas das tabelas local e atividade_roteiro de banco/01-esquema.sql.
ESQUEMA_DO_ROTEIRO = {
    "type": "object",
    "properties": {
        "dias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ordem": {"type": "integer", "description": "Número do dia, começando em 1"},
                    "atividades": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "nome": {"type": "string"},
                                "endereco": {"type": "string"},
                                "latitude": {"type": "number"},
                                "longitude": {"type": "number"},
                                "horario_funcionamento": {"type": "string"},
                                "hora_sugerida": {"type": "string", "description": "Formato HH:MM"},
                                "custo_estimado": {"type": "number", "description": "Na moeda local; 0 se gratuito"},
                                "categoria": {"type": "string", "enum": list(CATEGORIAS)},
                            },
                            "required": ["nome", "hora_sugerida", "categoria"],
                        },
                    },
                },
                "required": ["ordem", "atividades"],
            },
        }
    },
    "required": ["dias"],
}

INSTRUCOES_DO_SISTEMA = """\
Você é um planejador de viagens. Monta roteiros realistas, organizados por dia, \
para turistas brasileiros.

Regras:
- Sugira apenas lugares que existem de verdade no destino.
- Agrupe em cada dia lugares próximos entre si, para reduzir deslocamentos.
- Respeite os horários de funcionamento: não sugira um museu depois que ele fecha.
- Distribua as atividades ao longo do dia, em ordem cronológica, com horário no formato HH:MM.
- Informe latitude e longitude aproximadas, em graus decimais.
- Informe o custo estimado por pessoa na moeda local do destino; use 0 para atividades gratuitas.
- Use o nome em português quando houver um consagrado (ex.: Museu do Louvre); senão, o nome original.
- Não repita o mesmo lugar em dias diferentes.
- Classifique cada lugar em exatamente uma destas categorias: {categorias}.

Responda somente com um objeto JSON neste formato, sem texto antes ou depois:
{{"dias": [{{"ordem": 1, "atividades": [{{"nome": "...", "endereco": "...", \
"latitude": 0.0, "longitude": 0.0, "horario_funcionamento": "...", \
"hora_sugerida": "09:00", "custo_estimado": 0, "categoria": "Cultura"}}]}}]}}
""".format(categorias=", ".join(CATEGORIAS))

RITMO_DO_ESTILO = {
    "Tranquilo": "ritmo tranquilo, com tempo livre entre as atividades",
    "Equilibrado": "ritmo equilibrado",
    "Intenso": "ritmo intenso, aproveitando o dia inteiro",
}


def montar_pedido_ao_usuario(pedido):
    """Texto com os dados da viagem, enviado como mensagem do usuário."""
    linhas = [
        f"Destino: {pedido.destino}",
        f"Período: {pedido.datas[0]:%d/%m/%Y} a {pedido.datas[-1]:%d/%m/%Y} "
        f"({pedido.total_de_dias} dia{'s' if pedido.total_de_dias > 1 else ''})",
        f"Ritmo: {RITMO_DO_ESTILO.get(pedido.estilo, 'ritmo equilibrado')}",
        f"Atividades por dia: até {pedido.atividades_por_dia}",
    ]
    if pedido.preferencias:
        interesses = ", ".join(f"{categoria} ({nivel}/5)" for categoria, nivel in pedido.preferencias)
        linhas.append(f"Interesses, do maior para o menor (escala de 1 a 5): {interesses}")
        linhas.append("Dê mais espaço às categorias de interesse alto e evite as de interesse 1.")
    linhas.append(f"Monte o roteiro dos {pedido.total_de_dias} dias, numerados de 1 a {pedido.total_de_dias}.")
    return "\n".join(linhas)
