"""
Camada de aplicação (Figura 3 do Documento de Arquitetura).

- views.py: os Controllers do MVC, que recebem as requisições HTTP;
- serializers.py: os DTOs, que convertem objetos em JSON e validam entradas;
- servicos.py: o Service Layer, que orquestra cada caso de uso.

As views não contêm regra de negócio: validam a entrada, chamam um serviço e
devolvem o resultado serializado.
"""
