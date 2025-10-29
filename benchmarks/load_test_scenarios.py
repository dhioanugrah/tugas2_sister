from locust import HttpUser, task, between
class Q(HttpUser):
    wait_time = between(0.1, 0.5)
    @task
    def t(self):
        self.client.post('/queue/enqueue', json={'topic':'a','msg':{'x':1}})
        self.client.post('/queue/consume', json={'topic':'a','consumer_id':'c1'})
