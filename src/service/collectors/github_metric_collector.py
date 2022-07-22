import datetime as dt
from typing import Tuple
import requests
import concurrent
import concurrent.futures

from utils import chunkify, DateRange


GITHUB_DATETIME_STR_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
GIT_API_URL = 'https://api.github.com/repos'
GIT_HUB = 'github.com'

class GithubMetricCollector:
    """
    todo: pensar na interface dessa classe
    O repositorio de issues pode ser diferente do repositorio de codigo
    """

    def __init__(self, url, token=None):
        self.url = url
        self.user, self.repo = self.url_spliter(url)
        self.token = token

    @staticmethod
    def url_spliter(url):
        url_splitted = url.split('/')
        index = url_splitted.index(GIT_HUB)
        return url_splitted[index + 1: index + 3]

    # TODO: Mover para core
    # def get_team_throughput(self, start_date, end_date):
    #     date_now = dt.datetime.now().strftime(GITHUB_DATETIME_STR_FORMAT)
    #     issues = len(self.get_issues(start_date, end_date, ""))
    #     closedIssues = len(self.get_issues("", date_now, "state=closed"))
    #     return closedIssues/issues

    # def get_resolved_issues_throughput(self, start_date, end_date):

    #     # Todas as issues criadas dentro do período de tempo com o estado closed
    #     closed_issues = self.get_issues(start_date, end_date, "state=closed")

    #     # TODO: Tirar dúvida com o Danillo
    #     a = list(filter(lambda issue: issue["closed_at"] > start_date and issue["closed_at"] < end_date, closed_issues))

    #     return len(a) / len(closed_issues)

    # def get_issue_type_timeframe(self, start_date, end_date, type):
    #     total_issues = len(self.get_issues(start_date, end_date, ""))
    #     issues = len(self.get_issues(start_date, end_date, f"label={type}"))
    #     return issues/total_issues


    def get_number_of_issues_resolved_under_duration_threshold(self, date_range):
        """
        Pega todas as issues fechadas dentro de um período de tempo
        metric: number of issues resolved under the duration threshold
        """
        return self.get_issues(date_range, url_parm="state=closed")

    def get_number_of_issues_of_a_specific_label_under_duration_threshold(
        self,
        date_range: DateRange,
        label: str,
    ):
        """
        metric: number of issues of a specific type
        """
        self.get_issues(date_range, f"label={label}")

    def get_all_build_workflows_run_under_duration_threshold(
        self,
        date_range=None,
        build_pipeline_name='Build',
    ):
        response_json = self.request_git_api('actions/runs')

        # Issues and pull requests
        workflow_runs = []
        page = 1

        while True:
            response_json = self.request_git_api(
                f'actions/runs?per_page=100&page={page}'
            )

            if response_json['workflow_runs'] == []:
                break

            page += 1
            workflow_runs.extend(response_json['workflow_runs'])

        if date_range:
            workflow_runs = list(filter(
                lambda run: date_range.start <= run['created_at'] <= date_range.end,
                workflow_runs,
            ))

        workflow_runs = list(filter(
            lambda run: run['name'] == build_pipeline_name,
            workflow_runs,
        ))

        return workflow_runs

    def get_build_qty_and_time_sum_under_duration_threshold(
        self,
        date_range=None,
        build_pipeline_name='Build',

    ) -> Tuple[int, float]:
        """
        metrics:
            1. Total builds in a timeframe
            2. Feedback time for every build

        Returns:
            Retorna a quantidade de pipelines de build e o somatorio de tempo de execução
        """
        workflow_runs = self.get_all_build_workflows_run_under_duration_threshold(
            date_range,
            build_pipeline_name,
        )

        total_time_ms = 0

        chunks = chunkify(workflow_runs, 5)

        def process_chunk(chunk):
            total_time_ms = 0
            for run in chunk:
                if run is None:
                    break

                run_id = run['id']

                r = self.request_git_api(
                    f'actions/runs/{run_id}/timing'
                )
                total_time_ms += r['run_duration_ms']
            return total_time_ms

        with concurrent.futures.ThreadPoolExecutor() as executor:

            futures = [
                executor.submit(process_chunk, chunk)
                for chunk in chunks
            ]

            for future in concurrent.futures.as_completed(futures):
                total_time_ms += future.result()

        return len(workflow_runs), total_time_ms

    def get_total_number_of_issues_in_a_given_timeframe(
        self,
        date_range: DateRange,
    ) -> int:
        """
        metric: total number of issues in a given timeframe
        """
        return len(self.get_issues(date_range))

    def get_issues(
        self,
        date_range: DateRange = None,
        url_parm: str = None,
    ) -> list:
        """
        Retorna todas as issues dentro de um período de tempo
        metric: total number of issues in a given timeframe
        """
        if date_range and not isinstance(date_range.start, dt.datetime):
            raise TypeError('start_date must be a datetime object')

        if date_range and not isinstance(date_range.end, dt.datetime):
            raise TypeError('end_date must be a datetime object')

        if url_parm and not isinstance(url_parm, str):
            raise TypeError('url_parm must be a string')

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

        issues = [ ]
        for issue in issues_and_prs:
            created_at = dt.datetime.strptime(
                issue["created_at"],
                GITHUB_DATETIME_STR_FORMAT,
            )
            if 'pull_request' not in issue:
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
        if path.startswith('/'):
            path = path[1:]

        github_api = f'{GIT_API_URL}/{self.user}/{self.repo}/{path}'

        headers = {}

        if self.token:
            headers['Authorization'] = f'token {self.token}'

        github_response = requests.get(
            github_api,
            headers=headers,
        )

        return github_response.json()


if __name__ == '__main__':
    obj = GithubMetricCollector('https://github.com/fga-eps-mds/2022-1-MeasureSoftGram-Service/')


    begin = dt.datetime(2021, 7, 18, 19, 50, 55, 697558)
    end   = dt.datetime(2022, 7, 21, 21, 50, 55, 697558)

    print(obj.get_time_sum_of_all_build_pipelines('Run Tests'))
