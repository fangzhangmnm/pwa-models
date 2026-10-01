# PWA Models —— 家族模型权重的静态分发仓（curl 协议 + 哈希校验）

> created 2026-09-03 by Claude Fable 5.1（user 2026-09-03 拍板：托管 = GitHub + Hugging Face；信任根 = app 内钉的 manifest 哈希，主机只是运输）

给 PWA 家族（WebXiaoHeiWu 离线语音识别起步，为 weebpaint-genai 铺路）分发模型权重。**纯静态目录，任何能 `curl` 的主机都能镜像**；app 里不写死主机——app 钉的是每个包 `manifest.json` 的 sha256（= pack id），字节从哪来都先验再用（GitHub Pages / Hugging Face 镜像 / 用户自传 / OneDrive dump-load 同一套校验）。

## 布局

```
index.json                       # 包目录（slug / id / 体积 / 许可）
packs/<slug>/manifest.json       # v1：files 偏移表 + chunkBytes + chunks[{name,bytes,sha256}] + 整体 sha256 + engineConfig + license + source
packs/<slug>/chunk-000 …         # files 按序拼接后按 24 MiB 切片（= 想当镜像的主机里最小单文件上限：Cloudflare Pages 25 MiB；GitHub 50 MiB 警告线以下）
packs/<slug>/LICENSE.txt         # 打包当时的许可证快照（协议可能被上游单方修订，字节被钉住的是这一版）
voices/<id>.json                 # 音色定义：一个音色由哪几个包组成（必装的 + 每种语言另外要的）、每个包的 id、必须显示的署名与条款原文
```

打包：`python3 tools/pack.py …`（见文件头注释）。

## 命名与共享规矩（2026-10-01；家族根 CLAUDE.md「共享模型库」是原文）

- **包名** = `<种类>-<名字>-<规格或版本>-<yyyymmdd>`。种类是开放词表，现有：`asr`（语音识别模型）/ `voice`（一个音色的权重）/ `lang`（某种语言的文本前端：词典、分词器）/ `runtime`（推理运行时的 wasm）；以后的生成式模型照样往下加。日期 = 上游那一版的日期，自己构建的东西用构建日。最早的三个识别包没带种类前缀，不改名。
- **包只增、不改、不删。** 同一个包名的字节永远不变；要改就出新包名。删包只在 Pages 空间不够时由仓主决定。
- **拆小包、能共用的单独成包。** 运行时、某种语言的前端不跟着某一个模型走：别的模型、同源的别的 app 可以直接用缓存里已有的那一份。「一个音色 = 哪几个包」写在 `voices/<id>.json`，app 在 build 时把它和它点名的每个包的清单一起内嵌。
- **引擎的二进制可以进包**（哈希钉在 app 里，从哪下都一样安全）；JS 胶水是代码，留在 app / 库的仓里。
- **浏览器里的缓存**：同源的家族 app 共用一个 Cache Storage `pwa-models`（key = `/__pwa-models__/<包名>/<分片名>`，外加每个包一个 `verified.json`）；app 自己的缓存用自己的前缀，「清缓存」只清自己的前缀。
- 包里以 `.gz` 结尾的文件是压缩存放的（zlib 9 级），用之前解开。

## 包与许可（署名义务：使用时须注明出处并保留模型名）

| slug | 模型 | 许可 | 出处 |
|---|---|---|---|
| `sense-voice-small-int8-20240717` | SenseVoiceSmall（阿里巴巴通义实验室 / FunAudioLLM），int8，zh/en/ja/ko/yue，带标点 | FunASR Model Open Source License v1.1 | https://huggingface.co/FunAudioLLM/SenseVoiceSmall ；ONNX 导出 k2-fsa/sherpa-onnx |
| `dolphin-base-ctc-int8-20250402` | Dolphin-base（DataoceanAI & 清华大学），CTC 分支 int8，中文+22 方言+40 语 | Apache-2.0 | https://github.com/DataoceanAI/Dolphin ；ONNX 导出 k2-fsa/sherpa-onnx |
| `zipformer-streaming-zh-14M-int8-20230223` | Streaming Zipformer zh-14M（k2-fsa / icefall），流式中文 | Apache-2.0 | https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 |

识别包的运行时：sherpa-onnx WebAssembly（Apache-2.0）+ onnxruntime（MIT），vendored 在各 app 仓（如 WebXiaoHeiWu `vendor/sherpa-onnx-wasm/`）。

### 朗读音色

| 音色 | 由哪些包组成 | 下载 |
|---|---|---|
| `tsukuyomi-chan` つくよみちゃん（日 / 英 / 中；日语是训练语言，英 / 中是带日语口音的迁移） | `voice-tsukuyomi-chan-6lang-fp16-20260613` + `runtime-onnxruntime-web-1.30.0-20261001`；日语 `lang-ja-pyopenjtalk-plus-0.4.1.post9-20261001`；英语 `lang-en-cmudict-20261001`；中文 `lang-zh-pinyin-20261001` | 66.2 MB（37.8 + 3.5 + 23.3 + 0.8 + 0.7） |

| slug | 内容 | 许可 | 出处 |
|---|---|---|---|
| `voice-tsukuyomi-chan-6lang-fp16-20260613` | piper-plus 六语单音色模型（MB-iSTFT-VITS2，fp16）+ config，字节同上游 | **つくよみちゃんコーパス利用規約**（必须显示署名块和四条禁止用途，见包内 LICENSE.txt 与 `voices/tsukuyomi-chan.json`）；基础模型 CC-BY-4.0 | https://huggingface.co/ayousanz/piper-plus-tsukuyomi-chan @ `36b59c82`（2026-06-13） |
| `lang-ja-pyopenjtalk-plus-0.4.1.post9-20261001` | OpenJTalk 文本前端：自编 wasm（Emscripten）+ pyopenjtalk-plus 词典 + 读音模型 | Modified BSD（Open JTalk）+ BSD（MeCab）+ BSD-3 式（NAIST-jdic）+ MIT（pyopenjtalk-plus） | https://pypi.org/project/pyopenjtalk-plus/0.4.1.post9/ |
| `lang-en-cmudict-20261001` | CMU 发音词典 + 同形异音表（JSON） | BSD-2 式（CMUdict）+ Apache-2.0（g2p-en，格式转换过） | piper-plus `82ee4e7`、g2p-en 2.1.0 |
| `lang-zh-pinyin-20261001` | 单字 / 词组拼音表（声调数字式） | MIT（pypinyin / pinyin-data / phrase-pinyin-data） | piper-plus `82ee4e7`（声调标记转成了数字） |
| `runtime-onnxruntime-web-1.30.0-20261001` | onnxruntime-web 的 `ort-wasm-simd-threaded.wasm`（原样） | MIT（Microsoft） | npm `onnxruntime-web@1.30.0` |

**つくよみちゃん 的署名（app 必须显示在显眼处、字号够）**：

> 本ソフトウェアの音声合成には、フリー素材キャラクター「つくよみちゃん」（© Rei Yumesaki）が無料公開している音声データを使用しています。
> ■つくよみちゃんコーパス（CV.夢前黎）
> https://tyc.rei-yumesaki.net/material/corpus/

合成出来的声音禁止用于：批判・攻击他人；呼吁赞成或反对特定的政治立场・宗教・思想；不分级公开刺激性强的内容；以允许他人二次利用（当素材用）的形式公开。原文和条款页快照在音色包的 LICENSE.txt 里。拿这个模型去再分发或改造，同样受这份条款约束。

朗读的运行：JS 一侧在 `@internal/read-aloud`（家族内部库）；这几个包从打包到浏览器里合成的整链由该库的测试守着。

## 镜像

- 主源：本仓 GitHub Pages `https://fangzhangmnm.github.io/pwa-models/`
- 镜像：Hugging Face（待建）；用户也可整包下载后在 app 内自传，或经 OneDrive 在自己设备间搬运。
