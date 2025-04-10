import sys
import os
import hashlib
import zlib


def read_tree(tree_sha):
    object_dir = ".git/objects"
    dir_name = tree_sha[:2]
    file_name = tree_sha[2:]
    object_path = os.path.join(object_dir, dir_name, file_name)

    if not os.path.exists(object_path):
        raise FileNotFoundError(f"Object {tree_sha} not found.")

    with open(object_path, "rb") as f:
        data = f.read()

    decompressed_data = zlib.decompress(data)
    header, entries_data = decompressed_data.split(b'\0', 1)
    header_str = header.decode()

    if not header_str.startswith("tree"):
        raise ValueError(f"Invalid object type: {header_str}")

    entries = []
    while entries_data:
        mode_end = entries_data.find(b' ')
        name_end = entries_data.find(b'\0', mode_end + 1)
        sha = entries_data[name_end + 1: name_end + 21]
        name = entries_data[mode_end + 1:name_end].decode()
        mode = int(entries_data[:mode_end].decode(), 8)

        entries.append((mode, name, sha.hex()))
        entries_data = entries_data[name_end + 21:]

    return entries


def ls_tree(tree_sha, name_only=False):
    try:
        entries = read_tree(tree_sha)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    entries.sort(key=lambda entry: entry[1])

    for mode, name, sha in entries:
        if name_only:
            print(name)
        else:
            mode_str = f"{mode:06o}"
            type_str = "tree" if mode == 0o40000 else "blob"
            print(f"{mode_str} {type_str} {sha}\t{name}")


def hash_object(file_path, write=False):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        sys.exit(1)

    with open(file_path, "rb") as f:
        content = f.read()

    header = f"blob {len(content)}\0".encode()
    full_data = header + content
    sha1 = hashlib.sha1(full_data).hexdigest()

    if write:
        dir_name = sha1[:2]
        file_name = sha1[2:]
        object_dir = os.path.join(".git", "objects", dir_name)
        os.makedirs(object_dir, exist_ok=True)
        object_path = os.path.join(object_dir, file_name)

        if not os.path.exists(object_path):
            with open(object_path, "wb") as f:
                f.write(zlib.compress(full_data))

    print(sha1)


def cat_file(sha):
    object_dir = os.path.join(".git", "objects", sha[:2])
    object_path = os.path.join(object_dir, sha[2:])

    if not os.path.exists(object_path):
        print(f"Object {sha} not found.")
        sys.exit(1)

    with open(object_path, "rb") as f:
        data = zlib.decompress(f.read())

    header_end = data.find(b'\0')
    content = data[header_end + 1:]
    sys.stdout.buffer.write(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        os.makedirs(".git/objects", exist_ok=True)
        os.makedirs(".git/refs", exist_ok=True)
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    elif command == "hash-object":
        if len(sys.argv) == 4 and sys.argv[2] == "-w":
            file_path = sys.argv[3]
            hash_object(file_path, write=True)
        else:
            print("Usage: python script.py hash-object -w <file>")
            sys.exit(1)

    elif command == "cat-file":
        if len(sys.argv) == 4 and sys.argv[2] == "-p":
            sha = sys.argv[3]
            cat_file(sha)
        else:
            print("Usage: python script.py cat-file -p <sha>")
            sys.exit(1)

    elif command == "ls-tree":
        if len(sys.argv) == 4 and sys.argv[2] == "--name-only":
            tree_sha = sys.argv[3]
            ls_tree(tree_sha, name_only=True)
        elif len(sys.argv) == 3:
            tree_sha = sys.argv[2]
            ls_tree(tree_sha, name_only=False)
        else:
            print("Usage:\n  python script.py ls-tree <tree_sha>\n  python script.py ls-tree --name-only <tree_sha>")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
