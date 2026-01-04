import json
import re
import time

import requests


def get_latest_tag(tags, pattern):
    versions = []
    for tag in tags:
        if re.match(pattern, tag):
            versions.append(tag)
    versions.sort(reverse=True)
    return versions[0] if versions else None


urls = {
    "postgres": "https://registry.hub.docker.com/v2/repositories/library/postgres/tags/?page_size=100",
    "redis": "https://registry.hub.docker.com/v2/repositories/library/redis/tags/?page_size=100",
    "frequi": "https://registry.hub.docker.com/v2/repositories/freqtradeorg/frequi/tags/?page_size=100",
}

for name, url in urls.items():
    while True:
        try:
            response = requests.get(url)
            with open(f"{name}_tags.json", "w") as f:
                f.write(response.text)
            break
        except PermissionError:
            time.sleep(1)

for name, url in urls.items():
    with open(f"{name}_tags.json") as f:
        data = json.load(f)
    tags = [result["name"] for result in data["results"]]

    if name == "postgres":
        latest = get_latest_tag(tags, r"^\d+\.\d+-alpine$")
        print(f"Latest postgres: {latest}")
    elif name == "redis":
        latest = get_latest_tag(tags, r"^\d+\.\d+-alpine$")
        print(f"Latest redis: {latest}")
    elif name == "frequi":
        latest = get_latest_tag(tags, r"^\d{4}\.\d{2}$")
        print(f"Latest frequi: {latest}")
