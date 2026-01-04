import json
import re


def get_latest_tag(tags, pattern):
    versions = []
    for tag in tags:
        if re.match(pattern, tag):
            versions.append(tag)
    versions.sort(reverse=True)
    return versions[0] if versions else None


with open("postgres_tags.json") as f:
    postgres_data = json.load(f)

with open("redis_tags.json") as f:
    redis_data = json.load(f)

with open("frequi_tags.json") as f:
    frequi_data = f.read()

postgres_tags = [result["name"] for result in postgres_data["results"]]
redis_tags = [result["name"] for result in redis_data["results"]]

frequi_tags = re.findall(r'"name":\s*"([^"]+)"', frequi_data)

latest_postgres = get_latest_tag(postgres_tags, r"^\d+\.\d+-alpine$")
latest_redis = get_latest_tag(redis_tags, r"^\d+\.\d+-alpine$")
latest_frequi = get_latest_tag(frequi_tags, r"^\d{4}\.\d{2}$")

print(f"Latest postgres: {latest_postgres}")
print(f"Latest redis: {latest_redis}")
print(f"Latest frequi: {latest_frequi}")
