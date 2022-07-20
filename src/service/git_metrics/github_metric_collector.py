from datetime import datetime
import requests
GIT_API_URL = 'https://api.github.com'
GIT_HUB = 'github.com'

class GithubMetricCollector:

	def __init__(self, url):
		self.user = ''
		self.repo = ''
		self.url = url
		self.git_api = f"{GIT_API_URL}/repos"
		self.url_spliter()
		# TODO Pegar auth_key e auth_key do Front
		# self.auth_user = user
		# self.auth_key = auth_key

	def url_spliter(self):
		url_splitted = self.url.split('/')
		index = url_splitted.index(GIT_HUB)
		self.user, self.repo = url_splitted[index + 1: index + 3]

	def get_team_throughput(self, min_date, max_date): 
		issues = len(self.get_issues(min_date, max_date, ""))
		closedIssues = len(self.get_resolved_issues_throughput("", datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')))
		return closedIssues/issues

	def get_resolved_issues_throughput(self, min_date, max_date):
		issues = self.get_issues(min_date, max_date, "state=closed")
		return len(list(filter(lambda issue: issue["closed_at"] > min_date and issue["closed_at"] < max_date, issues)))/len(issues)

	def get_issue_type_timeframe(self, min_date, max_date, type):
		total_issues = len(self.get_issues(min_date, max_date, ""))
		issues = len(self.get_issues(min_date, max_date, f"label={type}"))
		return issues/total_issues

	def get_issues(self, min_date, max_date, url_parm):
		issues = []
		if min_date:
			issues = self.request_git_api(f"issues?since={min_date}&{url_parm}")
		else:
			issues = self.request_git_api(f"issues?{url_parm}")
		return list(filter(lambda issue: issue["created_at"] < max_date, issues))

	def request_git_api(self, path):
		github_api = f'{self.git_api}/{self.user}/{self.repo}/{path}'
		github_response = requests.get(f'{github_api}')
		# TODO Utilizar request com auth_key
		# github_response = requests.get(f'{github_api}', auth=(self.auth_user, self.auth_key))
		return github_response.json()