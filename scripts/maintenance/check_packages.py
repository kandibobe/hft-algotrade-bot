import toml


def get_deps():
    with open("pyproject.toml") as f:
        data = toml.load(f)

    deps = data["project"]["dependencies"]
    optional_deps = data["project"]["optional-dependencies"]

    all_deps = deps
    for group in optional_deps:
        all_deps += optional_deps[group]

    return all_deps


def write_reqs(deps):
    with open("requirements.txt", "w") as f:
        for dep in deps:
            f.write(dep + "\n")


if __name__ == "__main__":
    deps = get_deps()
    write_reqs(deps)
