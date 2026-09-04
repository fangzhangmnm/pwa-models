# PWA Models —— 家族模型权重的静态分发仓（curl 协议 + 哈希校验）

> created 2026-09-03 by Claude Fable 5.1（user 2026-09-03 拍板：托管 = GitHub + Hugging Face；信任根 = app 内钉的 manifest 哈希，主机只是运输）

给 PWA 家族（WebXiaoHeiWu 离线语音识别起步，为 weebpaint-genai 铺路）分发模型权重。**纯静态目录，任何能 `curl` 的主机都能镜像**；app 里不写死主机——app 钉的是每个包 `manifest.json` 的 sha256（= pack id），字节从哪来都先验再用（GitHub Pages / Hugging Face 镜像 / 用户自传 / OneDrive dump-load 同一套校验）。

## 布局

```
index.json                       # 包目录（slug / id / 体积 / 许可）
packs/<slug>/manifest.json       # v1：files 偏移表 + chunkBytes + chunks[{name,bytes,sha256}] + 整体 sha256 + engineConfig + license + source
packs/<slug>/chunk-000 …         # files 按序拼接后按 24 MiB 切片（= 想当镜像的主机里最小单文件上限：Cloudflare Pages 25 MiB；GitHub 50 MiB 警告线以下）
packs/<slug>/LICENSE.txt         # 打包当时的许可证快照（协议可能被上游单方修订，字节被钉住的是这一版）
```

打包：`python3 tools/pack.py …`（见文件头注释）。

## 包与许可（署名义务：使用时须注明出处并保留模型名）

| slug | 模型 | 许可 | 出处 |
|---|---|---|---|
| `sense-voice-small-int8-20240717` | SenseVoiceSmall（阿里巴巴通义实验室 / FunAudioLLM），int8，zh/en/ja/ko/yue，带标点 | FunASR Model Open Source License v1.1 | https://huggingface.co/FunAudioLLM/SenseVoiceSmall ；ONNX 导出 k2-fsa/sherpa-onnx |
| `dolphin-base-ctc-int8-20250402` | Dolphin-base（DataoceanAI & 清华大学），CTC 分支 int8，中文+22 方言+40 语 | Apache-2.0 | https://github.com/DataoceanAI/Dolphin ；ONNX 导出 k2-fsa/sherpa-onnx |
| `zipformer-streaming-zh-14M-int8-20230223` | Streaming Zipformer zh-14M（k2-fsa / icefall），流式中文 | Apache-2.0 | https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 |

运行时：sherpa-onnx WebAssembly（Apache-2.0）+ onnxruntime（MIT），vendored 在各 app 仓（如 WebXiaoHeiWu `vendor/sherpa-onnx-wasm/`）。

## 镜像

- 主源：本仓 GitHub Pages `https://fangzhangmnm.github.io/pwa-models/`
- 镜像：Hugging Face（待建）；用户也可整包下载后在 app 内自传，或经 OneDrive 在自己设备间搬运。
