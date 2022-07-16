import requests
GIT_API_URL = 'https://api.github.com'
GIT_HUB = 'github.com'

class GithubMetricCollector:
	def __init__(self, url, user, auth_key):
		self.__metrics = {}
		self.__url = url
		self.__git_api = f"{GIT_API_URL}/repos"
		self.__url_spliter()
		self.user = user
		self.auth_key = auth_key

	def __url_spliter(self):
		url_splitted = self.__url.split('/')
		index = url_splitted.index(GIT_HUB)
		self.user, self.repo = url_splitted[index + 1: index + 3]

	def get_metrics(self):
		return self.__metrics

	def set_yearly_commits(self):
		response = self.__request_git_api('stats/contributors')
		commits = 0

		for i in range(0, len(response['all'])):
			commits = commits + response['all'][i];    
		
		self.__metrics['yearly_commits'] = commits

	def set_health_percentage(self):
		response = self.__request_git_api('community/profile')
		self.__metrics['health_percentage'] = response['health_percentage']
		
	def __request_git_api(self, path):
		github_api = f'{self.__git_api}/{self.user}/{self.repo}/{path}'
		github_response = requests.get(f'{github_api}', auth=(self.user, self.auth_key))
		return github_response.json()