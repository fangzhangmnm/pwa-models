#!/usr/bin/env python3
# tools/pack.py —— 把一组模型文件打成「静态可 curl 的分片包」：files 按序拼接 → 固定大小切片 → manifest.json
# （逐片 sha256 + 整体 sha256 + 文件偏移表 + 引擎加载配置 + 许可证快照 + 出处）。
# 信任根 = app 里钉的 manifest sha256（pack 的 id 就是它）；任何主机/用户自传/OneDrive 都只是运输，字节到手先验再用。
# 切片 24 MiB = 想当镜像的主机里最小的单文件上限（Cloudflare Pages 25 MiB；GitHub 50 MiB 警告线以下）。
# created 2026-09-03 by Claude Fable 5.1
#
# 用法：python3 tools/pack.py <pack-slug> --file <path>[=<name-in-pack>]... --engine-config <json-file-or-inline>
#         --name "..." --task asr --lang zh,en --license-name "..." --license-file <txt> --attribution "..."
#         --source-model <url> --source-converted <url> [--out packs] [--chunk-bytes N]
import argparse, hashlib, json, os, sys, time

CHUNK_DEFAULT = 24 * 1024 * 1024

def sha256_file_slices(paths):
    """Yield (path, size) and build the concatenation stream lazily."""
    for p in paths:
        yield p, os.path.getsize(p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--file", action="append", required=True, help="path[=name-in-pack]")
    ap.add_argument("--engine", default="sherpa-onnx")
    ap.add_argument("--engine-config", required=True, help="JSON (inline or @file): how the app instantiates the engine; file names refer to name-in-pack")
    ap.add_argument("--name", required=True)
    ap.add_argument("--task", default="asr")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--license-name", required=True)
    ap.add_argument("--license-file", required=True)
    ap.add_argument("--attribution", required=True)
    ap.add_argument("--source-model", required=True)
    ap.add_argument("--source-converted", default="")
    ap.add_argument("--source-file", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--out", default="packs")
    ap.add_argument("--chunk-bytes", type=int, default=CHUNK_DEFAULT)
    a = ap.parse_args()

    files = []
    for spec in a.file:
        path, _, name = spec.partition("=")
        name = name or os.path.basename(path)
        files.append((path, name))
    cfg = a.engine_config
    engine_config = json.load(open(cfg[1:])) if cfg.startswith("@") else json.loads(cfg)

    out_dir = os.path.join(a.out, a.slug)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.startswith("chunk-"): os.remove(os.path.join(out_dir, old))

    # 拼接流：逐文件读，喂给「当前切片」；切片满就落盘 + 记 sha256。同时算整体 sha256 与每文件 sha256。
    chunk_bytes = a.chunk_bytes
    chunks, file_entries = [], []
    total_h = hashlib.sha256()
    cur = bytearray(); cur_h = hashlib.sha256(); offset = 0

    def flush():
        nonlocal cur, cur_h
        if not cur: return
        name = f"chunk-{len(chunks):03d}"
        with open(os.path.join(out_dir, name), "wb") as f: f.write(cur)
        chunks.append({"name": name, "bytes": len(cur), "sha256": cur_h.hexdigest()})
        cur = bytearray(); cur_h = hashlib.sha256()

    for path, name in files:
        size = os.path.getsize(path); fh = hashlib.sha256()
        file_entries.append({"path": name, "bytes": size, "offset": offset, "sha256": None})
        with open(path, "rb") as f:
            while True:
                room = chunk_bytes - len(cur)
                buf = f.read(min(room, 8 * 1024 * 1024))
                if not buf: break
                cur += buf; cur_h.update(buf); total_h.update(buf); fh.update(buf); offset += len(buf)
                if len(cur) >= chunk_bytes: flush()
        file_entries[-1]["sha256"] = fh.hexdigest()
    flush()

    lic_text = open(a.license_file, encoding="utf-8").read()
    with open(os.path.join(out_dir, "LICENSE.txt"), "w", encoding="utf-8") as f: f.write(lic_text)

    manifest = {
        "v": 1,
        "slug": a.slug,
        "name": a.name,
        "task": a.task,
        "lang": a.lang.split(","),
        "engine": a.engine,
        "engineConfig": engine_config,
        "files": file_entries,
        "chunkBytes": chunk_bytes,
        "chunks": chunks,
        "totalBytes": offset,
        "sha256": total_h.hexdigest(),
        "license": {"name": a.license_name, "file": "LICENSE.txt", "sha256": hashlib.sha256(lic_text.encode()).hexdigest(), "attribution": a.attribution},
        "source": {"model": a.source_model, "converted": a.source_converted, "file": a.source_file},
        "notes": a.notes,
        "createdAt": time.strftime("%Y-%m-%d"),
        "createdBy": "tools/pack.py (Claude Fable 5.1)",
    }
    body = json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f: f.write(body)
    pack_id = hashlib.sha256(body.encode()).hexdigest()
    print(json.dumps({"slug": a.slug, "packId(sha256 of manifest.json)": pack_id, "totalBytes": offset, "chunks": len(chunks), "files": [e["path"] for e in file_entries]}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
