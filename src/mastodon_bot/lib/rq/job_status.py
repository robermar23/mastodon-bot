from redis import Redis
from rq.job import Job

redis_conn = "redis://default:8ckxHVNZGnqu@127.0.0.1:6379/1"
job_id = "74d4e01d-4a7a-4f9b-af8a-18823ae4332c"

redis = Redis.from_url(redis_conn)
job = Job.fetch(job_id, connection=redis)
print(f"Status: {job.get_status()}")
print(f"Result: {job.result}")
print(f"Args: {job.args}")
print(f"kwargs: {job.kwargs}")
print(f"Error: {job.exc_info}")

