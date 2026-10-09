# Shimano

Shimano 是一个正在开发的个人语音助手。当前可运行的部分位于 `SenseVoice/`：它能持续监听、用本地 VAD 截取语音、本地识别文字、按“爱莉”唤醒、调用兼容 OpenAI Chat Completions 的模型接口，并用系统语音分段朗读回复。界面显示 `Listening / Thinking / Speaking`；播报时可用唤醒称呼插话打断。

| 目录 | 用途 | 当前运行是否依赖 |
| --- | --- | --- |
| `SenseVoice/` | Shimano 自己的 Python / PySide6 练习原型；包含界面、语音、对话代码和本地模型 | 是 |
| `ARCHITECTURE.md` | 数据流、文件职责与协作边界 | 文档 |
| `THIRD_PARTY.md` | 第三方来源与许可线索 | 文档 |

从这里开始：[架构与模块分工](ARCHITECTURE.md)；首次安装及运行方法见 [SenseVoice 使用说明](SenseVoice/README.md)。新成员可在 `SenseVoice/` 中创建 Python 3.12 虚拟环境、安装 `requirements.txt`，再运行 `download_models.py --sample` 获取本地语音资源。API 密钥在文字测试窗口填写，保存在本机 `.env.local`，不要提交到 Git。

当前已形成基础对话闭环，但还是独立的练习原型：没有桌宠/Live2D 形象、持久对话记忆、声纹识别或播报中打断。Sakura 的桌面程序与插件并未接入这个运行链路，也不包含在本仓库中；保留必要的许可署名和来源说明。
