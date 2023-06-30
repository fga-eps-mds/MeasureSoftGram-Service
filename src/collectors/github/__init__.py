"""
Módulo que define as classes que interagem diretamente com a API do GitHub.

O objetivo é que todos os interessados nas métricas do GitHub somente
interajam com essa classe, que abstrai a API do GitHub.
"""
import concurrent
import concurrent.futures
import datetime as dt
from typing import Iterable, List

import requests

from utils import DateRange, chunkify
from utils.decorators import lru_cache_time

GITHUB_DATETIME_STR_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
GIT_API_URL = "https://api.github.com/repos"
GIT_HUB = "github.com"


@lru_cache_time(60 * 5)
def cached_get_request(*args, **kwargs):
    headers = {}
    if kwargs["token"]:
        token = kwargs.pop("token")
        headers["Authorization"] = f"token {token}"
    return requests.get(*args, **kwargs, headers=headers)


class GithubMetricCollector:
    def __init__(self, url, token=None):
        self.url = url
        self.user, self.repo = self.url_spliter(url)
        self.token = token

    @staticmethod
    def url_spliter(url):
        url_splitted = url.split("/")
        index = url_splitted.index(GIT_HUB)
        return url_splitted[index + 1 : index + 3]

    @staticmethod
    def str_to_datetime(date_str):
        return dt.datetime.strptime(date_str, GITHUB_DATETIME_STR_FORMAT)

    def get_number_of_issues_resolved_in_the_last_x_days(
        self,
        x: int,
        label: str = "",
    ) -> int:
        """
        metric: number of issues resolved in the last x days
        """
        if not isinstance(x, int):
            raise ValueError("x must be an integer")

        if not isinstance(label, str):
            raise ValueError("label must be a string")

        date_range = DateRange.create_from_today(x)

        return len(self.get_issues(date_range, f"state=closed&labels={label}"))

    def get_number_of_issues_with_such_labels_in_the_last_x_days(
        self,
        x: int,
        labels: List[str],
    ) -> int:
        if not isinstance(x, int):
            raise ValueError("x must be an integer")

        # Se a lista for vazia ou ao menos um item não for uma string
        if not labels or any(not isinstance(label, str) for label in labels):
            raise ValueError("labels must be a list of strings")

        labels: str = ",".join(labels)

        date_range = DateRange.create_from_today(x)

        return len(self.get_issues(date_range, f"labels={labels}"))

    def get_total_number_of_issues_in_the_last_x_days(
        self, x: int, label: str = ""
    ) -> int:
        """
        metric: total number of issues in a given timeframe
        """
        if not isinstance(x, int):
            raise ValueError("x must be an integer")

        if not isinstance(label, str):
            raise ValueError("label must be a string")

        date_range = DateRange.create_from_today(x)

        return len(self.get_issues(date_range, f"labels={label}"))

    def __get_all_build_pipelines_executed_in_the_last_x_days(
        self,
        x: int,
        build_pipeline_names: List[str],
    ):
        """
        metric: number of build workflows run in the last x days
        """
        if not isinstance(x, int):
            raise ValueError("x must be an integer")

        if not build_pipeline_names or any(
            not isinstance(pipeline_name, str) for pipeline_name in build_pipeline_names
        ):
            raise ValueError("build_pipeline_names must be a list of strings")

        workflow_runs = []
        page = 1

        while True:
            response_json = self.request_git_api(
                f"actions/runs?per_page=100&page={page}"
            )

            # TODO: workflow_runs devia sempre está na response_json
            if (
                "workflow_runs" not in response_json
                or response_json["workflow_runs"] == []
            ):
                break

            page += 1

            workflow_runs.extend(response_json["workflow_runs"])

        date = DateRange.create_from_today(x)

        # Filtra as execuções dentro do período de tempo
        workflow_runs = filter(
            lambda run: (
                date.start <= self.str_to_datetime(run["created_at"]) <= date.end
            ),
            workflow_runs,
        )

        workflow_runs = filter(
            lambda run: run["name"] in build_pipeline_names, workflow_runs
        )

        return tuple(workflow_runs)

    def get_the_number_of_build_pipelines_executed_in_the_last_x_days(
        self,
        x: int,
        build_pipeline_names: Iterable[str],
    ) -> int:
        """
        metrics: Total builds in a timeframe

        Returns:
            A quantidade de pipelines de build nos últimos x dias
        """
        build_pipeline_names = tuple(build_pipeline_names)

        workflow_runs = self.__get_all_build_pipelines_executed_in_the_last_x_days(
            x,
            build_pipeline_names,
        )

        return len(workflow_runs)

    def get_the_sum_of_their_durations_in_the_last_x_days(
        self,
        x: int,
        build_pipeline_names: Iterable[str],
    ) -> float:
        """
        metrics: Feedback time for every build

        Returns:
            O somatorio de tempo de execução das pipelines de build
            nos últimos x dias
        """
        build_pipeline_names = tuple(build_pipeline_names)

        workflow_runs = self.__get_all_build_pipelines_executed_in_the_last_x_days(
            x,
            build_pipeline_names,
        )

        # No máximo 5 requisições simultâneas
        chunks = chunkify(workflow_runs, 5)

        # python closure for parallelize the github api requests
        def process_chunk(chunk):
            total_time_ms = 0
            for run in chunk:
                if run is None:
                    break

                run_id = run["id"]

                response_json = self.request_git_api(f"actions/runs/{run_id}/timing")
                total_time_ms += response_json["run_duration_ms"]
            return total_time_ms

        total_time_ms = 0

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_chunk, chunk) for chunk in chunks]

            for future in concurrent.futures.as_completed(futures):
                total_time_ms += future.result()

        return total_time_ms

    def get_issues(
        self,
        date_range: DateRange = None,
        url_parm: str = None,
    ) -> list:
        """
        Retorna todas as issues dentro de um período de tempo
        metric: total number of issues in a given timeframe
        """
        if url_parm and not isinstance(url_parm, str):
            raise TypeError("url_parm must be a string")

        # Issues and pull requests
        issues_and_prs = []
        page = 1

        while True:
            response_json = self.request_git_api(
                f"issues?per_page=100&page={page}&{url_parm}"
            )
            if response_json == []:
                break

            page += 1
            issues_and_prs.extend(response_json)

        issues = []
        for issue in issues_and_prs:
            created_at = dt.datetime.strptime(
                issue["created_at"],
                GITHUB_DATETIME_STR_FORMAT,
            )
            if "pull_request" not in issue:
                if date_range:
                    if date_range.start <= created_at <= date_range.end:
                        issues.append(issue)
                else:
                    issues.append(issue)

        return issues

    def request_git_api(self, path) -> dict:
        """
        Faz uma requisição para um endpoint do github
        e retorna a response já convertido em dicionário python
        """
        if path.startswith("/"):
            path = path[1:]

        github_api = f"{GIT_API_URL}/{self.user}/{self.repo}/{path}"

        headers = {}

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        github_response = cached_get_request(
            url=github_api,
            token=self.token,
        )

        return github_response.json()
