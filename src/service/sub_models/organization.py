from django.contrib.auth import get_user_model
from django.db import models


class Organization(models.Model):
    """
    Tabela que armazena os dados das organizações do sistema
    """
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )
    members = models.ManyToManyField(
        get_user_model(),
        related_name='organizations',
        blank=True,
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Produto de software é a abstração de um
    software que está sendo desenvolvido/mantido

    Observação: Anteriormente se chamava Project, mas o cliente achou
    melhor mudar esse nome, pois uma vez que o projeto é finalizado o
    resultado é o produto de software.
    """
    class Meta:
        unique_together = (('name', 'organization'),)

    name = models.CharField(max_length=128)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products',
    )

    def __str__(self):
        return self.name


class Repository(models.Model):
    """
    Um repositório é sempre de um projeto. Uma vez que um projeto pode ser
    composto de vários repositórios de código, como por exemplo o
    repositório do backend e do frontend.
    """
    class Meta:
        unique_together = (('name', 'product'),)
        verbose_name_plural = 'Repositories'

    name = models.CharField(max_length=128)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='repositories',
    )

    def __str__(self):
        return self.name
