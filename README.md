# 🧠 PyGit — минималистичная реализация Git на Python

Этот проект представляет собой простую реализацию основных функций Git на Python. Он позволяет инициализировать репозиторий, создавать объекты (`blob`, `tree`, `commit`), хэшировать файлы, читать содержимое объектов и даже **клонировать** репозиторий с сервера, поддерживающего `git-upload-pack`.

## 🚀 Возможности

- `init` — инициализация Git-репозитория  
- `hash-object -w <file>` — хэширование и сохранение объекта `blob`  
- `cat-file -p <sha>` — просмотр содержимого объекта по его SHA-1  
- `write-tree` — создание `tree`-объекта  
- `commit-tree <tree_sha> -p <parent_commit> -m <message>` — создание коммита  
- `ls-tree --name-only <tree_sha>` — список содержимого дерева  
- `clone <url> <dir>` — клонирование удалённого репозитория (ограниченно)

## 📦 Установка

```bash
git clone https://github.com/yourusername/pygit.git
cd pygit
python3 pygit.py init
```
💡 Зависимости: только стандартная библиотека Python, никаких внешних пакетов.


## 📂 Примеры использования

### Инициализация репозитория
```
python3 main.py init
```

### Хэширование файла и запись объекта
```
python3 main.py hash-object -w example.txt
```
Вывод: e69de29bb2d1d6434b8b29ae775ad8c2e48c5391

### Просмотр содержимого объекта
```
python3 main.py cat-file -p <sha>
```

### Создание дерева (tree) и коммита (commit)
```
python3 main.py write-tree

Вывод: <tree_sha>

python3 main.py commit-tree <tree_sha> -p <parent_sha> -m "Initial commit"
Вывод: <commit_sha>
```
### Просмотр содержимого дерева
```
python3 main.py ls-tree --name-only <tree_sha>
```

### Клонирование репозитория (экспериментально)
```
python3 main.py clone https://example.com/my-repo.git my-repo
```

## 🛠 Структура проекта

* init_repo() — инициализация .git каталога
* write_object() / read_object() — чтение и запись 
* git-объектов (blob, tree, commit)
* write-tree — обход текущей директории и создание дерева (tree)
* commit-tree — создание коммита с указанием родителя и сообщения
* clone — базовая реализация git-клонирования через HTTP-протокол (git-upload-pack)
* Поддержка zlib, SHA-1, pack-файлов и ref-delta объектов

## ⚠️ Ограничения

* Нет поддержки индекса (index), веток, слияний, pull/push и конфигураций
* Поддержка clone работает только с серверами, предоставляющими info/refs и git-upload-pack
* Нет проверки подписи коммитов, хука или разрешения конфликтов
* Отсутствует полноценная CLI-подсистема (используются sys.argv)
