from google.oauth2 import service_account
from google.cloud import bigquery

class BigQueryClient:
	class __BigQueryClient:
		def __init__(self):
			self.credentials = service_account.Credentials.from_service_account_file("./medhack2020-b2f3ee3bbaf3.json", scopes=["https://www.googleapis.com/auth/cloud-platform"])
			self.client = bigquery.Client(credentials=self.credentials, project=self.credentials.project_id)

		def query(self, qstring):
			return self.client.query(qstring).result()

	instance = None

	def __init__(self):
		if BigQueryClient.instance is None:
			BigQueryClient.instance =BigQueryClient. __BigQueryClient()

	def __getattr__(self, name):
		return getattr(self.instance, name)

	def query(self, qstring):
		return BigQueryClient.instance.query(qstring)

