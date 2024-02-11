FILENAME = "requirements.in"
file_content = {}

with open(FILENAME, 'r') as reqfile:
    for line in reqfile:
        req = line.strip().split("==")
        if req[0] in file_content:
            print(f"Removing duplicate entry {req[0]}=={min(file_content[req[0]], req[1])}")
            file_content[req[0]] = max(file_content[req[0]], req[1])
        else:
            file_content[req[0]] = req[1]

with open(FILENAME, 'w') as reqfile:
    for req, version in file_content.items():
        reqfile.write(f"{req}=={version}\n")