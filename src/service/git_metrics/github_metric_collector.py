from platform import release
import requests
GIT_API_URL = 'https://api.github.com'
GIT_HUB = 'github.com'

class GithubMetricCollector:
	def __init__(self, url):
		self.__metrics = {}
		self.__url = url
		self.__git_api = f"{GIT_API_URL}/repos"
		self.__last_release_date = self.__request_git_api('releases')[-1]['published_at']
		self.__url_spliter()
		# TODO Pegar auth_key e user do Front
		# self.user = user
		# self.auth_key = auth_key

	def __url_spliter(self):
		url_splitted = self.__url.split('/')
		index = url_splitted.index(GIT_HUB)
		self.user, self.repo = url_splitted[index + 1: index + 3]

	def get_metrics(self):
		self.__set_health_percentage()
		self.__set_release_issues()
		self.__set_release_commits()
		return self.__metrics

	def __set_release_commits(self):
		commitsResponse = self.__request_git_api(f"commits?since={self.__last_release_date}")
		self.__metrics['commits_by_release'] = len(commitsResponse)

	def __set_release_issues(self):
		commitsResponse = self.__request_git_api(f"issues?state=closed&since={self.__last_release_date}")
		self.__metrics['release_issues'] = len(commitsResponse)

	def __set_health_percentage(self):
		response = self.__request_git_api('community/profile')
		self.__metrics['health_percentage'] = response['health_percentage']

	def __request_git_api(self, path):
		github_api = f'{self.__git_api}/{self.user}/{self.repo}/{path}'
		github_response = requests.get(f'{github_api}')
		# TODO Utilizar request com auth_key
		# github_response = requests.get(f'{github_api}', auth=(self.user, self.auth_key))
		return github_response.json()
		
	def __metric_formater(self, id, value):
		metric_format = {
				"metric_id": id,
				"value": value,
		}
		return metric_format