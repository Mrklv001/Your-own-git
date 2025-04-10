import sys
import os
import hashlib
import zlib


def read_blob(blob_sha):
    # Получаем путь к объекту по хешу
    object_dir = ".git/objects"
    dir_name = blob_sha[:2]  # Первые два символа хеша
    file_name = blob_sha[2:]  # Остальные символы хеша
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


def hash_object(file_path):
    # Чтение содержимого файла
    with open(file_path, "rb") as f:
        content = f.read()

    # Размер содержимого
    size = len(content)

    # Формирование строки для хеширования
    header = f"blob {size}\0".encode()  # Заголовок "blob <size>\0"
    object_data = header + content

    # Вычисление SHA-1 хеша
    sha1_hash = hashlib.sha1(object_data).hexdigest()

    # Путь к файлу в .git/objects
    object_dir = ".git/objects"
    dir_name = sha1_hash[:2]  # Первые два символа хеша
    file_name = sha1_hash[2:]  # Остальные символы хеша
    object_path = os.path.join(object_dir, dir_name)

    # Создаем директорию, если ее нет
    os.makedirs(object_path, exist_ok=True)

    # Сжимаем данные с помощью zlib
    compressed_data = zlib.compress(object_data)

    # Пишем сжатые данные в файл
    with open(os.path.join(object_path, file_name), "wb") as f:
        f.write(compressed_data)

    # Выводим хеш
    print(sha1_hash)


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
        # Проверяем, что указан флаг -p и хеш объекта
        if len(sys.argv) < 4 or sys.argv[2] != "-p":
            print("Usage: python script.py cat-file -p <blob_sha>")
            sys.exit(1)

        blob_sha = sys.argv[3]
        try:
            read_blob(blob_sha)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "hash-object":
        # Проверяем, что указан файл
        if len(sys.argv) < 4 or sys.argv[2] != "-w":
            print("Usage: python script.py hash-object -w <file>")
            sys.exit(1)

        file_path = sys.argv[3]
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found.")
            sys.exit(1)

        hash_object(file_path)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
