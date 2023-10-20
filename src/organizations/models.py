from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

from pre_configs.models import PreConfig
from utils import staticfiles


class Organization(models.Model):

    name = models.CharField(max_length=128)
    key = models.SlugField(max_length=128, unique=True)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )
    members = models.ManyToManyField(
        get_user_model(),
        related_name="organizations",
        blank=True,
    )

    def save(self, *args, **kwargs):
        # A KEY é gerada somente na criação do objeto
        if not self.key:
            self.key = slugify(self.name)

            # if Organization.objects.filter(key=self.key).exists():
            #     random_num = uuid4().hex[:6]
            #     self.key = f'{self.key}-{random_num}'

        return super().save(*args, **kwargs)

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
        unique_together = (("key", "organization"),)

    name = models.CharField(max_length=128)
    key = models.SlugField(max_length=128, unique=True)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="products",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.name)
            self.key = f"{self.organization.key}-{self.key}"

            # if Product.objects.filter(key=self.key).exists():
            #     random_num = uuid4().hex[:6]
            #     self.key = f'{self.key}-{random_num}'

        super().save(*args, **kwargs)

        PreConfig.objects.get_or_create(
            name="Default pre-config", data=staticfiles.DEFAULT_PRE_CONFIG, product=self
        )


class Repository(models.Model):
    """
    Um repositório é sempre de um projeto. Uma vez que um projeto pode ser
    composto de vários repositórios de código, como por exemplo o
    repositório do backend e do frontend.
    """

    class Meta:
        unique_together = (("key", "product"),)
        verbose_name_plural = "Repositories"

    name = models.CharField(max_length=128)
    key = models.SlugField(max_length=128, unique=True)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="repositories",
    )

    def save(self, *args, **kwargs):
        self.key = slugify(self.name)
        self.key = f"{self.product.key}-{self.key}"
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
