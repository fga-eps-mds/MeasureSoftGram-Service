import requests
GIT_API_URL = 'https://api.github.com'
GIT_HUB = 'github.com'

class GithubMetricCollector:

	metrics_types = ['commits_by_release', 'release_issues', 'health_percentage']

	def __init__(self, url):
		self.metrics = {}
		self.user = ''
		self.repo = ''
		self.url = url
		self.git_api = f"{GIT_API_URL}/repos"
		self.url_spliter()
		self.last_release_date = self.get_last_release_date()
		# TODO Pegar auth_key e auth_key do Front
		# self.auth_user = user
		# self.auth_key = auth_key

	def get_last_release_date(self):
		releases = self.request_git_api('releases')
		if len(releases) > 0:
			return releases[-1]['published_at']
		else: 
			return ""

	def url_spliter(self):
		url_splitted = self.url.split('/')
		index = url_splitted.index(GIT_HUB)
		self.user, self.repo = url_splitted[index + 1: index + 3]

	def get_metrics(self):
		self.set_health_percentage()
		self.set_release_issues()
		self.set_release_commits()
		return self.metrics

	def set_release_commits(self):
		date = ""
		if self.last_release_date != None: 
			date = f"?since={self.last_release_date}"
		commitsResponse = self.request_git_api(f"commits{date}")
		self.metrics['commits_by_release'] = len(commitsResponse)

	def set_release_issues(self):
		date = ""
		if self.last_release_date != None: 
			date = f"&since={self.last_release_date}"
		commitsResponse = self.request_git_api(f"issues?state=closed{date}")
		self.metrics['release_issues'] = len(commitsResponse)

	def set_health_percentage(self):
		response = self.request_git_api('community/profile')
		self.metrics['health_percentage'] = response['health_percentage']

	def request_git_api(self, path):
		github_api = f'{self.git_api}/{self.user}/{self.repo}/{path}'
		github_response = requests.get(f'{github_api}')
		# TODO Utilizar request com auth_key
		# github_response = requests.get(f'{github_api}', auth=(self.auth_user, self.auth_key))
		return github_response.json()