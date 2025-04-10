from operator import itemgetter
import sys
import zlib
import hashlib
import struct
from pathlib import Path
from typing import Tuple, List, cast
import urllib.request


def init_repo(parent: Path):
    (parent / ".git").mkdir(parents=True)
    (parent / ".git" / "objects").mkdir(parents=True)
    (parent / ".git" / "refs").mkdir(parents=True)
    (parent / ".git" / "refs" / "heads").mkdir(parents=True)
    (parent / ".git" / "HEAD").write_text("ref: refs/heads/main\n")


def read_object(parent: Path, sha: str) -> Tuple[str, bytes]:
    pre = sha[:2]
    post = sha[2:]
    p = parent / ".git" / "objects" / pre / post
    bs = p.read_bytes()
    head, content = zlib.decompress(bs).split(b"\0", maxsplit=1)
    ty, _ = head.split(b" ")
    return ty.decode(), content


def write_object(parent: Path, ty: str, content: bytes) -> str:
    content = ty.encode() + b" " + f"{len(content)}".encode() + b"\0" + content
    hash = hashlib.sha1(content, usedforsecurity=False).hexdigest()
    compressed_content = zlib.compress(content, level=zlib.Z_BEST_SPEED)
    pre = hash[:2]
    post = hash[2:]
    p = parent / ".git" / "objects" / pre / post
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(compressed_content)
    return hash


def main():
    match sys.argv[1:]:
        case ["init"]:
            init_repo(Path("."))
            print("Initialized git directory")
        case ["cat-file", "-p", blob_sha]:
            _, content = read_object(Path("."), blob_sha)
            sys.stdout.buffer.write(content)
        case ["hash-object", "-w", path]:
            hash = write_object(Path("."), "blob", Path(path).read_bytes())
            print(hash)
        case ["ls-tree", "--name-only", tree_sha]:
            items = []
            _, contents = read_object(Path("."), tree_sha)
            while contents:
                mode, contents = contents.split(b" ", 1)
                name, contents = contents.split(b"\0", 1)
                sha = contents[:20]
                contents = contents[20:]
                items.append((mode.decode(), name.decode(), sha.hex()))
            for _, name, _ in items:
                print(name)
        case ["write-tree"]:
            parent = Path(".")

            def toEntry(p: Path, exclude_git: bool = False) -> Tuple[str, str, str]:
                mode = "40000" if p.is_dir() else "100644"
                if p.is_dir():
                    entries: List[Tuple[str, str, str]] = []
                    for child in p.iterdir():
                        if exclude_git and child.name == ".git":
                            continue
                        entries.append(toEntry(child))
                    s_entries = sorted(entries, key=itemgetter(1))
                    b_entries = b"".join(
                        m.encode() + b" " + n.encode() + b"\0" + bytes.fromhex(h)
                        for (m, n, h) in s_entries
                    )
                    hash = write_object(parent, "tree", b_entries)
                    return (mode, p.name, hash)
                else:
                    hash = write_object(parent, "blob", p.read_bytes())
                    return (mode, p.name, hash)
            (_, _, hash) = toEntry(Path(".").absolute(), True)
            print(hash)
        case ["commit-tree", tree_sha, "-p", commit_sha, "-m", message]:
            contents = b"".join(
                [
                    b"tree %b\n" % tree_sha.encode(),
                    b"parent %b\n" % commit_sha.encode(),
                    b"author ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n",
                    b"committer ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n\n",
                    message.encode(),
                    b"\n",
                ]
            )
            hash = write_object(Path("."), "commit", contents)
            print(hash)
        case ["clone", url, dir]:
            parent = Path(dir)
            init_repo(parent)
            # fetch refs
            req = urllib.request.Request(
                f"{url}/info/refs?service=git-upload-pack")
            with urllib.request.urlopen(req) as f:
                refs = {
                    bs[1].decode(): bs[0].decode()
                    for bs0 in cast(bytes, f.read()).split(b"\n")
                    if (bs1 := bs0[4:])
                    and not bs1.startswith(b"#")
                    and (bs2 := bs1.split(b"\0")[0])
                    and (bs := (bs2[4:] if bs2.endswith(b"HEAD") else bs2).split(b" "))
                }
            # render refs
            for name, sha in refs.items():
                Path(parent / ".git" / name).write_text(sha + "\n")
            # fetch pack
            body = (
                b"0011command=fetch0001000fno-progress"
                + b"".join(b"0032want " + ref.encode() +
                           b"\n" for ref in refs.values())
                + b"0009done\n0000"
            )
            req = urllib.request.Request(
                f"{url}/git-upload-pack",
                data=body,
                headers={"Git-Protocol": "version=2"},
            )
            with urllib.request.urlopen(req) as f:
                pack_bytes = cast(bytes, f.read())
            pack_lines = []
            while pack_bytes:
                line_len = int(pack_bytes[:4], 16)
                if line_len == 0:
                    break
                pack_lines.append(pack_bytes[4:line_len])
                pack_bytes = pack_bytes[line_len:]
            pack_file = b"".join(l[1:] for l in pack_lines[1:])

            def next_size_type(bs: bytes) -> Tuple[str, int, bytes]:
                ty = (bs[0] & 0b_0111_0000) >> 4
                match ty:
                    case 1:
                        ty = "commit"
                    case 2:
                        ty = "tree"
                    case 3:
                        ty = "blob"
                    case 4:
                        ty = "tag"
                    case 6:
                        ty = "ofs_delta"
                    case 7:
                        ty = "ref_delta"
                    case _:
                        ty = "unknown"
                size = bs[0] & 0b_0000_1111
                i = 1
                off = 4
                while bs[i - 1] & 0b_1000_0000:
                    size += (bs[i] & 0b_0111_1111) << off
                    off += 7
                    i += 1
                return ty, size, bs[i:]

            def next_size(bs: bytes) -> Tuple[int, bytes]:
                size = bs[0] & 0b_0111_1111
                i = 1
                off = 7
                while bs[i - 1] & 0b_1000_0000:
                    size += (bs[i] & 0b_0111_1111) << off
                    off += 7
                    i += 1
                return size, bs[i:]
            # get objs
            pack_file = pack_file[8:]  # strip header and version
            n_objs, *_ = struct.unpack("!I", pack_file[:4])
            pack_file = pack_file[4:]
            for _ in range(n_objs):
                ty, _, pack_file = next_size_type(pack_file)
                match ty:
                    case "commit" | "tree" | "blob" | "tag":
                        dec = zlib.decompressobj()
                        content = dec.decompress(pack_file)
                        pack_file = dec.unused_data
                        write_object(parent, ty, content)
                    case "ref_delta":
                        obj = pack_file[:20].hex()
                        pack_file = pack_file[20:]
                        dec = zlib.decompressobj()
                        content = dec.decompress(pack_file)
                        pack_file = dec.unused_data
                        target_content = b""
                        base_ty, base_content = read_object(parent, obj)
                        # base and output sizes
                        _, content = next_size(content)
                        _, content = next_size(content)
                        while content:
                            is_copy = content[0] & 0b_1000_0000
                            if is_copy:
                                data_ptr = 1
                                offset = 0
                                size = 0
                                for i in range(0, 4):
                                    if content[0] & (1 << i):
                                        offset |= content[data_ptr] << (i * 8)
                                        data_ptr += 1
                                for i in range(0, 3):
                                    if content[0] & (1 << (4 + i)):
                                        size |= content[data_ptr] << (i * 8)
                                        data_ptr += 1
                                # do something with offset and size
                                content = content[data_ptr:]
                                target_content += base_content[offset: offset + size]
                            else:
                                size = content[0]
                                append = content[1: size + 1]
                                content = content[size + 1:]
                                # do something with append
                                target_content += append
                        write_object(parent, base_ty, target_content)
                    case _:
                        raise RuntimeError("Not implemented")
            # render tree

            def render_tree(parent: Path, dir: Path, sha: str):
                dir.mkdir(parents=True, exist_ok=True)
                _, tree = read_object(parent, sha)
                while tree:
                    mode, tree = tree.split(b" ", 1)
                    name, tree = tree.split(b"\0", 1)
                    sha = tree[:20].hex()
                    tree = tree[20:]
                    match mode:
                        case b"40000":
                            render_tree(parent, dir / name.decode(), sha)
                        case b"100644":
                            _, content = read_object(parent, sha)
                            Path(dir / name.decode()).write_bytes(content)
                        case _:
                            raise RuntimeError("Not implemented")
            _, commit = read_object(parent, refs["HEAD"])
            tree_sha = commit[5: 40 + 5].decode()
            render_tree(parent, parent, tree_sha)


if __name__ == "__main__":
    main()
