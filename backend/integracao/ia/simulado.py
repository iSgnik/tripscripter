"""
Cliente de IA simulado: monta o roteiro sem chamar nenhum serviço externo.

Serve a três propósitos:
- reserva na apresentação, se a internet falhar ou a cota gratuita acabar;
- desenvolvimento sem chave de API;
- testes automatizados, que não devem consumir cota.

Para Paris, Tóquio e Lisboa usa os mesmos locais dos dados de exemplo
(banco/02-dados-exemplo.sql), com coordenadas, para que apareçam no mapa.
Para outros destinos, devolve sugestões genéricas, sem coordenadas.
"""

import unicodedata

from .base import ClienteIA

# (nome, endereço, latitude, longitude, horário de funcionamento, custo, categoria)
CATALOGO = {
    "paris": [
        ("Museu do Louvre", "Rue de Rivoli, 75001 Paris", 48.8606, 2.3376, "Quarta a segunda, 9h às 18h", 22, "Arte"),
        ("Marché des Enfants Rouges", "39 Rue de Bretagne, 75003 Paris", 48.8630, 2.3625, "Terça a domingo, 8h30 às 19h30", 18, "Gastronomia"),
        ("Jardim de Luxemburgo", "75006 Paris", 48.8462, 2.3372, "Diariamente, do amanhecer ao pôr do sol", 0, "Natureza"),
        ("Bistrot Paul Bert", "18 Rue Paul Bert, 75011 Paris", 48.8527, 2.3835, "Terça a sábado, 12h às 14h e 19h30 às 23h", 45, "Gastronomia"),
        ("Montmartre", "75018 Paris", 48.8846, 2.3380, "Acesso livre", 0, "Cultura"),
        ("Basílica de Sacré-Cœur", "35 Rue du Chevalier de la Barre, 75018", 48.8867, 2.3431, "Diariamente, 6h30 às 22h30", 0, "Cultura"),
        ("Canal Saint-Martin", "75010 Paris", 48.8709, 2.3658, "Acesso livre", 0, "Natureza"),
        ("Musée de l'Orangerie", "Jardin des Tuileries, 75001 Paris", 48.8638, 2.3226, "Quarta a segunda, 9h às 18h", 12, "Arte"),
        ("Livraria Shakespeare and Company", "37 Rue de la Bûcherie, 75005 Paris", 48.8526, 2.3471, "Diariamente, 10h às 22h", 0, "Cultura"),
    ],
    "toquio": [
        ("Templo Sensō-ji", "2-3-1 Asakusa, Taito, Tóquio", 35.7148, 139.7967, "Diariamente, 6h às 17h", 0, "Cultura"),
        ("Rua Nakamise", "1-36-3 Asakusa, Taito, Tóquio", 35.7118, 139.7966, "Diariamente, 9h às 19h", 0, "Gastronomia"),
        ("Museu Nacional de Tóquio", "13-9 Uenokoen, Taito, Tóquio", 35.7188, 139.7766, "Terça a domingo, 9h30 às 17h", 1000, "Arte"),
        ("Parque Ueno", "Uenokoen, Taito, Tóquio", 35.7156, 139.7745, "Diariamente, 5h às 23h", 0, "Natureza"),
        ("Jardim Nacional Shinjuku Gyoen", "11 Naitomachi, Shinjuku, Tóquio", 35.6852, 139.7100, "Terça a domingo, 9h às 16h30", 500, "Natureza"),
        ("Omoide Yokocho", "1-2 Nishishinjuku, Shinjuku, Tóquio", 35.6938, 139.6996, "Diariamente, 17h às 23h", 3000, "Vida noturna"),
        ("Bairro de Yanaka", "Yanaka, Taito, Tóquio", 35.7276, 139.7661, "Acesso livre", 0, "Cultura"),
        ("Mirante de Shibuya", "2-24-12 Shibuya, Tóquio", 35.6580, 139.7016, "Diariamente, 10h às 22h30", 2500, "Vida noturna"),
        ("Monte Takao", "Takaomachi, Hachioji, Tóquio", 35.6253, 139.2436, "Acesso livre; teleférico das 8h às 17h45", 1400, "Natureza"),
    ],
    "lisboa": [
        ("Mosteiro dos Jerónimos", "Praça do Império, 1400-206 Lisboa", 38.6977, -9.2065, "Terça a domingo, 10h às 17h30", 10, "Cultura"),
        ("Torre de Belém", "Av. Brasília, 1400-038 Lisboa", 38.6916, -9.2160, "Terça a domingo, 10h às 17h30", 8, "Cultura"),
        ("Time Out Market", "Av. 24 de Julho 49, 1200-479 Lisboa", 38.7072, -9.1458, "Diariamente, 10h às 24h", 25, "Gastronomia"),
        ("Castelo de São Jorge", "R. de Santa Cruz, 1100-129 Lisboa", 38.7139, -9.1334, "Diariamente, 9h às 21h", 15, "Cultura"),
        ("Bairro de Alfama", "Alfama, Lisboa", 38.7118, -9.1300, "Acesso livre", 0, "Cultura"),
        ("Miradouro da Senhora do Monte", "Largo Monte, 1170-253 Lisboa", 38.7193, -9.1325, "Acesso livre", 0, "Natureza"),
        ("LX Factory", "R. Rodrigues de Faria 103, 1300-501 Lisboa", 38.7036, -9.1786, "Diariamente, 9h às 24h", 0, "Arte"),
        ("Oceanário de Lisboa", "Esplanada Dom Carlos I, 1990-005 Lisboa", 38.7635, -9.0937, "Diariamente, 10h às 19h", 25, "Natureza"),
    ],
}

# Sugestões usadas quando o destino não está no catálogo.
GENERICAS = (
    ("Centro histórico de {cidade}", "Cultura"),
    ("Museu principal de {cidade}", "Arte"),
    ("Mercado municipal de {cidade}", "Gastronomia"),
    ("Parque central de {cidade}", "Natureza"),
    ("Mirante com vista de {cidade}", "Natureza"),
    ("Restaurante de culinária típica em {cidade}", "Gastronomia"),
    ("Bairro boêmio de {cidade}", "Vida noturna"),
    ("Passeio guiado a pé por {cidade}", "Cultura"),
)

HORARIOS = ("09:00", "11:30", "14:00", "16:30", "19:30", "21:00")


def normalizar(texto):
    """'Tóquio, Japão' → 'toquio'. Ignora acentos, maiúsculas e o país."""
    cidade = texto.split(",")[0].strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", cidade) if unicodedata.category(c) != "Mn")


class ClienteIASimulado(ClienteIA):
    nome = "Simulado"

    def sugerir_roteiro(self, pedido):
        cidade = pedido.destino.split(",")[0].strip()
        catalogo = CATALOGO.get(normalizar(pedido.destino))
        if catalogo is None:
            catalogo = [(modelo.format(cidade=cidade), None, None, None, None, None, categoria) for modelo, categoria in GENERICAS]

        # Distribui os locais entre os dias, sem repetir. Se a viagem for
        # longa, os últimos dias ficam vazios — o usuário completa à mão.
        dias = []
        restantes = list(catalogo)
        for ordem in range(1, pedido.total_de_dias + 1):
            do_dia, restantes = restantes[: pedido.atividades_por_dia], restantes[pedido.atividades_por_dia :]
            dias.append(
                {
                    "ordem": ordem,
                    "atividades": [
                        {
                            "nome": nome,
                            "endereco": endereco,
                            "latitude": latitude,
                            "longitude": longitude,
                            "horario_funcionamento": horario,
                            "hora_sugerida": HORARIOS[posicao],
                            "custo_estimado": custo,
                            "categoria": categoria,
                        }
                        for posicao, (nome, endereco, latitude, longitude, horario, custo, categoria) in enumerate(do_dia)
                    ],
                }
            )
        return {"dias": dias}
