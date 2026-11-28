**`bin/vh new` 不再需要 rsync：精简的 Linux 上也建得出 canvas-film 和手绘项目**
- Why: 在一台云端容器（Ubuntu 24.04.5，x86_64）上，`bin/vh new … --engine canvas-film`、长讲解、照片回顾、教程和手绘类的项目都建不出来，报 `rsync: command not found`；Docker 镜像和精简的 Linux 默认没有 rsync，`bin/vh doctor` 也不查它。
- 复制引擎模板、Three.js 层和手绘引擎改用 Python 自带的 `shutil.copytree`（Python 3 本来就是必需的）：时间和权限照旧保留，`out`、`node_modules` 照旧不复制，任何一层都不复制，和原来 `rsync -a --exclude` 一样。
