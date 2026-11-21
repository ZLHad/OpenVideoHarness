**连不上官方源时，安装自动改用国内镜像，之后的下载都跟着走**
- Why: 在国内网络下，第一次安装和第一次做片要连 npm、PyPI、Hugging Face、GitHub Releases 和 Google 的存储；原来要照 wiki 手动设三四个变量、另跑两条命令装 Chrome，Studio 应用的 Electron 下载没有写怎么办。
- 安装时先试官方的 npm 源（5 秒）；没有应答、国内镜像有，就改用国内镜像，用一句话说明，并记在这台机器自己的设置里（`~/.config/ovh/settings.json`）。不按语言或时区猜。`--mirror cn` 直接用，`--mirror off` 不用，也记下来。
- 镜像的地址集中在 `tools/mirrors.txt` 一个文件里，每一行写明是谁在运营（npmmirror.com、清华 TUNA、hf-mirror.com）。镜像打开时，`bin/vh` 给它运行的每条命令设好 npm、uv（Python 包和 Python 本身）、Hugging Face 和 Electron 的镜像变量；你自己设过的变量不动。HyperFrames 下载 Chrome 时没有可设的地址，所以由 `bin/vh new` 和安装先从镜像把它装进 HyperFrames 找的目录。
- 新命令 `bin/vh settings`：看这台机器的设置，`bin/vh settings mirror cn|off|auto` 改镜像，`--json` 给 Studio 的设置面板读。`bin/vh doctor` 多一行说现在走哪里、怎么关。
- 已有的校验不变，也不信任镜像：npm ci 按 lockfile 里的哈希核对每个包；Electron 按它自己的包里带的 checksums.json 核对。uv 的包、Hugging Face 的模型、Python 和 Chrome 没有钉住的哈希，和从官方源下一样照收。
- 切到镜像以后，uv 会按新的源重新下载之前缓存过的 Python 包（它的缓存按源区分）。
