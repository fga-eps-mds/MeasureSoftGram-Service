"""Schema OpenAPI das respostas montadas à mão em `accounts.views` (só documentação)."""

from rest_framework import serializers


class GitHubOrganizationSerializer(serializers.Serializer):
    """A conta pessoal (primeiro item) e as organizações; campos vêm da API do GitHub e podem faltar."""

    github_org_id = serializers.IntegerField(allow_null=True)
    github_org_name = serializers.CharField(allow_null=True, allow_blank=True)
    avatar_url = serializers.CharField(allow_null=True, allow_blank=True)
    description = serializers.CharField(allow_null=True, allow_blank=True)


class GitLabNamespaceSerializer(serializers.Serializer):
    """O usuário (`kind: user`, primeiro item) e os grupos (`kind: group`)."""

    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField(allow_null=True, allow_blank=True)
    full_path = serializers.CharField(allow_null=True, allow_blank=True)
    avatar_url = serializers.CharField(allow_null=True, allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    kind = serializers.ChoiceField(choices=("user", "group"))


class ProviderValidateSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    reason = serializers.CharField(required=False, help_text="Só com valid=false.")
