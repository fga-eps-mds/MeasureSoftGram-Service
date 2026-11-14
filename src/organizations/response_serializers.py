"""Schema OpenAPI das listas de repositórios dos provedores (só documentação)."""

from rest_framework import serializers


class GitHubRepoSerializer(serializers.Serializer):
    """`GitHubReposViewSet._paged_response`; campos vêm da API do GitHub e podem faltar."""

    github_repo_id = serializers.IntegerField(allow_null=True)
    github_full_name = serializers.CharField(allow_null=True, allow_blank=True)
    name = serializers.CharField(allow_null=True, allow_blank=True)
    description = serializers.CharField(allow_null=True, allow_blank=True)
    url = serializers.CharField(allow_null=True, allow_blank=True)


class GitLabProjectSerializer(serializers.Serializer):
    """`GitLabProjectsViewSet._serialize_projects`."""

    gitlab_project_id = serializers.IntegerField(allow_null=True)
    gitlab_path_with_namespace = serializers.CharField(allow_null=True, allow_blank=True)
    name = serializers.CharField(allow_null=True, allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    url = serializers.CharField(allow_null=True, allow_blank=True)


class QualityBandResponseSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=("E", "D", "C", "B", "A"))
    min = serializers.FloatField()
    max = serializers.FloatField()


class QualityBandsResponseSerializer(serializers.Serializer):
    """`quality_bands.serialize`."""

    is_default = serializers.BooleanField()
    can_edit = serializers.BooleanField()
    bands = QualityBandResponseSerializer(many=True)
