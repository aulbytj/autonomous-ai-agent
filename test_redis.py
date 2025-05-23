import redis
import json

# Connect to Redis
redis_client = redis.from_url("redis://localhost:6379")

# List all keys in Redis
keys = redis_client.keys("task:*")
print(f"Found {len(keys)} task keys in Redis:")
for key in keys:
    print(f"  - {key.decode('utf-8')}")

# Get the latest task
if keys:
    latest_key = keys[-1]
    task_data = redis_client.get(latest_key)
    if task_data:
        print(f"\nTask data for {latest_key.decode('utf-8')}:")
        task_dict = json.loads(task_data.decode('utf-8'))
        print(json.dumps(task_dict, indent=2))
    else:
        print(f"\nNo data found for key {latest_key.decode('utf-8')}")
else:
    print("\nNo task keys found in Redis")
