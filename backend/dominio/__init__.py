"""
Camada de domínio (Figura 3 do Documento de Arquitetura).

Concentra as regras de negócio do TripScripter. Não importa nada do Django
nem do banco de dados: recebe e devolve valores simples. Isso permite testar
as regras isoladamente e mantê-las iguais se a forma de armazenamento mudar.
"""
