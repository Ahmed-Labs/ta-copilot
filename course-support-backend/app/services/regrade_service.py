from app.models.regrade_models import RegradeRequest

fake_regrade_requests: list[RegradeRequest] = []

def get_all_regrade_requests():
    return fake_regrade_requests

def add_regrade_request(request: RegradeRequest):
    fake_regrade_requests.append(request)
    return request
