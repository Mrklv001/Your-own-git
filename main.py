import sys
import os
import hashlib
import zlib


def init():
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")


def hash_object(data, obj_type="blob", write=True):
    header = f"{obj_type} {len(data)}".encode() + b'\0'
    full_data = header + data
    sha = hashlib.sha1(full_data).hexdigest()

    if write:
        dir_name = sha[:2]
        file_name = sha[2:]
        object_dir = os.path.join(".git", "objects", dir_name)
        os.makedirs(object_dir, exist_ok=True)
        object_path = os.path.join(object_dir, file_name)

        if not os.path.exists(object_path):
            with open(object_path, "wb") as f:
                f.write(zlib.compress(full_data))

    return sha


def hash_object_cmd(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    sha = hash_object(data)
    print(sha)


def cat_file(sha):
    object_path = os.path.join(".git", "objects", sha[:2], sha[2:])
    if not os.path.exists(object_path):
        print(f"Object {sha} not found.")
        sys.exit(1)

    with open(object_path, "rb") as f:
        decompressed = zlib.decompress(f.read())

    header_end = decompressed.find(b'\0')
    content = decompressed[header_end + 1:]
    sys.stdout.buffer.write(content)


def read_tree(tree_sha):
    path = os.path.join(".git", "objects", tree_sha[:2], tree_sha[2:])
    if not os.path.exists(path):
        raise FileNotFoundError(f"Object {tree_sha} not found.")

    with open(path, "rb") as f:
        data = zlib.decompress(f.read())

    header, body = data.split(b'\0', 1)
    if not header.decode().startswith("tree"):
        raise ValueError("Not a tree object.")

    entries = []
    while body:
        space = body.find(b' ')
        null = body.find(b'\0', space)
        mode = int(body[:space].decode())
        name = body[space + 1:null].decode()
        sha = body[null + 1:null + 21].hex()
        entries.append((mode, name, sha))
        body = body[null + 21:]

    return entries


def ls_tree(tree_sha, name_only=False):
    try:
        entries = read_tree(tree_sha)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if name_only:
        entries = [entry[1] for entry in entries]
        entries.sort()
        for name in entries:
            print(name)
    else:
        for mode, name, sha in sorted(entries, key=lambda x: x[1]):
            type_str = "tree" if mode == 40000 else "blob"
            print(f"{mode:06o} {type_str} {sha}\t{name}")


def write_tree_recursive(path="."):
    entries = []

    for item in sorted(os.listdir(path)):
        if item == ".git":
            continue

        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            mode = "40000"
            sha = write_tree_recursive(full_path)
        else:
            mode = "100644"
            with open(full_path, "rb") as f:
                data = f.read()
            sha = hash_object(data)

        entry = f"{mode} {item}".encode() + b'\0' + bytes.fromhex(sha)
        entries.append(entry)

    body = b''.join(entries)
    return hash_object(body, obj_type="tree", write=True)


def write_tree():
    sha = write_tree_recursive(".")
    print(sha)


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init()
    elif command == "hash-object":
        if len(sys.argv) >= 4 and sys.argv[2] == "-w":
            filepath = sys.argv[3]
            hash_object_cmd(filepath)
        else:
            print("Usage: hash-object -w <file>")
            sys.exit(1)
    elif command == "cat-file":
        if len(sys.argv) == 4 and sys.argv[2] == "-p":
            cat_file(sys.argv[3])
        else:
            print("Usage: cat-file -p <sha>")
            sys.exit(1)
    elif command == "ls-tree":
        if len(sys.argv) == 4 and sys.argv[2] == "--name-only":
            ls_tree(sys.argv[3], name_only=True)
        else:
            print("Usage: ls-tree --name-only <tree_sha>")
            sys.exit(1)
    elif command == "write-tree":
        write_tree()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
