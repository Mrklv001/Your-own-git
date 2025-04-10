import sys
import os
import zlib


def read_blob(blob_sha):
    # Получаем путь к объекту по хешу
    object_dir = ".git/objects"
    dir_name = blob_sha[:2]  # Первые два символа хеша
    file_name = blob_sha[2:]  # Оставшиеся 38 символов хеша
    object_path = os.path.join(object_dir, dir_name, file_name)

    if not os.path.exists(object_path):
        raise FileNotFoundError(f"Object {blob_sha} not found.")

    # Чтение содержимого объекта
    with open(object_path, "rb") as f:
        data = f.read()

    # Распаковка данных с помощью zlib
    decompressed_data = zlib.decompress(data)

    # Формат: "blob <size>\0<content>"
    header, content = decompressed_data.split(b'\0', 1)

    # Проверяем, что это действительно blob
    header_str = header.decode()
    if not header_str.startswith("blob"):
        raise ValueError(f"Invalid object type: {header_str}")

    # Печатаем содержимое (контент) без новой строки
    sys.stdout.write(content.decode())


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    elif command == "cat-file":
        # Проверяем, что аргументов достаточно
        if len(sys.argv) < 3:
            print("Usage: python script.py cat-file -p <blob_sha>")
            sys.exit(1)

        flag = sys.argv[2]

        if flag == "-p" and len(sys.argv) >= 4:
            blob_sha = sys.argv[3]
            try:
                read_blob(blob_sha)
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Error: Unknown flag or missing object hash")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
