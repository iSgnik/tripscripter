"""
GeradorRoteiroService (Figura 2 do Documento de Arquitetura) — RQ004.

Fluxo da geração:

    1. montar o pedido com destino, datas, ritmo e preferências do usuário;
    2. pedir a sugestão ao cliente de IA configurado;
    3. se ele falhar, pedir ao cliente de reserva (o simulado, por padrão);
    4. validar a sugestão (dominio/roteirizacao.py);
    5. gravar locais e atividades no banco, numa única transação.

A chamada à IA acontece fora da transação de propósito: ela pode levar vários
segundos, e manter o banco travado durante esse tempo não traz nenhum ganho.
"""

import logging
import time as relogio
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from comum.excecoes import ConflitoDeEstado, ServicoIndisponivel
from dominio import roteirizacao
from integracao.ia import ErroNoServicoDeIA, PedidoDeRoteiro
from integracao.ia import fabrica
from persistencia.models import AtividadeRoteiro, Local

registro = logging.getLogger(__name__)

# Distância máxima, em graus, para considerar que dois locais com o mesmo nome
# são o mesmo ponto (cerca de 1 km). Evita fundir o "Museu Nacional" de duas
# cidades diferentes.
TOLERANCIA_DE_COORDENADA = Decimal("0.01")


@dataclass
class ResultadoDaGeracao:
    provedor: str           # quem gerou o roteiro: Groq, Gemini ou Simulado
    aviso: str | None       # preenchido quando foi usada a reserva
    tempo_em_ms: int        # tempo total, para conferir o RQ009
    total_de_atividades: int


class GeradorRoteiroService:
    def __init__(self, viagem, cliente=None, reserva=None):
        """
        cliente e reserva podem ser informados nos testes. Se omitidos, vêm da
        configuração do .env (integracao/ia/fabrica.py).
        """
        self.viagem = viagem
        self._cliente = cliente
        self._reserva = reserva if cliente is not None else fabrica.criar_reserva()

    # -- passos do fluxo -------------------------------------------------------

    def montar_prompt(self):
        """Reúne os dados da viagem e do usuário no pedido enviado à IA."""
        preferencias = self.viagem.usuario.preferencias.order_by("-nivel_interesse", "categoria")
        return PedidoDeRoteiro(
            destino=self.viagem.destino,
            datas=[dia.data for dia in self.viagem.dias.order_by("ordem")],
            estilo=self.viagem.estilo_viagem,
            atividades_por_dia=roteirizacao.atividades_por_dia(self.viagem.estilo_viagem),
            preferencias=[(p.categoria, p.nivel_interesse) for p in preferencias],
        )

    def validar_locais(self, sugestao, pedido):
        return roteirizacao.validar_sugestao(sugestao, pedido.total_de_dias, pedido.atividades_por_dia)

    def _pedir_sugestao(self, cliente, pedido):
        sugestao = cliente.sugerir_roteiro(pedido)
        return self.validar_locais(sugestao, pedido)

    def gerar_roteiro(self, substituir=False):
        if not substituir and AtividadeRoteiro.objects.filter(dia__viagem=self.viagem).exists():
            raise ConflitoDeEstado(
                "Este roteiro já tem atividades. Envie substituir=true para gerar um novo, "
                "o que apaga as atividades e notas atuais."
            )

        inicio = relogio.perf_counter()
        pedido = self.montar_prompt()
        aviso = None

        try:
            cliente = self._cliente or fabrica.criar_cliente_principal()
            dias = self._pedir_sugestao(cliente, pedido)
        except (ErroNoServicoDeIA, roteirizacao.RespostaDeIAInvalida) as falha:
            # O motivo técnico vai para o log do servidor; o usuário recebe
            # uma mensagem simples. A chave de API nunca aparece em nenhum dos dois.
            registro.warning("Falha na geração do roteiro da viagem %s: %s", self.viagem.pk, falha)
            if self._reserva is None:
                raise ServicoIndisponivel(
                    "O serviço de inteligência artificial não está disponível no momento. Tente novamente."
                ) from falha
            cliente = self._reserva
            dias = self._pedir_sugestao(cliente, pedido)
            aviso = (
                "O serviço de inteligência artificial não respondeu. "
                "Este roteiro foi montado com sugestões pré-definidas."
            )

        total = self._gravar(dias)
        return ResultadoDaGeracao(
            provedor=cliente.nome,
            aviso=aviso,
            tempo_em_ms=round((relogio.perf_counter() - inicio) * 1000),
            total_de_atividades=total,
        )

    # -- gravação -------------------------------------------------------------

    @transaction.atomic
    def _gravar(self, dias_sugeridos):
        # Apaga o roteiro anterior; as notas saem junto (ON DELETE CASCADE).
        AtividadeRoteiro.objects.filter(dia__viagem=self.viagem).delete()

        total = 0
        for dia, atividades in zip(self.viagem.dias.order_by("ordem"), dias_sugeridos):
            for posicao, dados in enumerate(atividades, start=1):
                AtividadeRoteiro.objects.create(
                    dia=dia,
                    local=self._local_do_catalogo(dados),
                    hora_sugerida=dados["hora_sugerida"],
                    ordem_do_dia=posicao,
                    custo_estimado=dados["custo_estimado"],
                )
                total += 1
        return total

    def _local_do_catalogo(self, dados):
        """
        Reaproveita o local se ele já estiver no catálogo; senão, cria. É o
        reaproveitamento que justifica a tabela local ser separada de
        atividade_roteiro (banco/README).
        """
        local = self._buscar_no_catalogo(dados)
        if local is None:
            return Local.objects.create(
                nome=dados["nome"],
                endereco=dados["endereco"],
                latitude=dados["latitude"],
                longitude=dados["longitude"],
                horario_funcionamento=dados["horario_funcionamento"],
                categoria=dados["categoria"],
            )
        # Completa a categoria de um local antigo que ainda não a tinha. Uma
        # categoria já gravada não é trocada pela da IA.
        if local.categoria is None and dados["categoria"] is not None:
            local.categoria = dados["categoria"]
            local.save(update_fields=["categoria"])
        return local

    def _buscar_no_catalogo(self, dados):
        for local in Local.objects.filter(nome__iexact=dados["nome"]):
            if dados["latitude"] is None or local.latitude is None:
                if local.endereco == dados["endereco"]:
                    return local
            elif (
                abs(local.latitude - dados["latitude"]) <= TOLERANCIA_DE_COORDENADA
                and abs(local.longitude - dados["longitude"]) <= TOLERANCIA_DE_COORDENADA
            ):
                return local
        return None
