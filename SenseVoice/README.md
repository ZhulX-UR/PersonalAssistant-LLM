# Shimano 语音对话原型

这里独立练习语音对话，不依赖 Sakura 的桌面程序或插件市场。语音在本机完成 VAD 与 SenseVoice 识别；开启自动回复后，只有唤醒后的识别文字会发给配置的模型服务，麦克风音频不会上传给该对话接口。

## 从源码首次运行（Windows）

建议安装 Python 3.12，进入本目录后运行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_models.py --sample
.\.venv\Scripts\python.exe gui.py
```

模型权重约 239 MB，下载脚本还会获取词表、VAD 模型和可选示例音频；下载后进行 SHA-256 校验，已校验的文件会复用。资源放在 `models/` 和 `samples/`，不纳入 Git。若无需“试用示例”按钮，可省略 `--sample`。VS Code 解释器选 `.venv\Scripts\python.exe`。`启动界面.cmd` 和 `启动LLM测试.cmd` 在完成上述环境安装后可直接双击使用。

## 独立 LLM 文字对话测试

双击 `启动LLM测试.cmd`。窗口可选“硅基流动”或“自定义兼容接口”，填写模型 ID、角色提示词，并在密码输入框填入 API Key。点击“保存设置与密钥”后，供应商、模型、提示词保存在 `llm_settings.json`；密钥保存在本机 `.env.local`，界面只显示“已保存”，不会回显密钥。两个文件都已加入 `.gitignore`。无需另建文件，也不要把密钥发到聊天里。

硅基流动使用官方 `https://api.siliconflow.cn/v1/chat/completions`；默认模型 ID 是官方文档示例 `deepseek-ai/DeepSeek-V4-Flash`。服务商可能调整可用模型，请以账户中的模型列表为准，可在界面直接改成你有权限使用的 ID。自定义接口按同样的 chat/completions 协议工作；远程地址须为 HTTPS，本机 Ollama 一类服务可使用 `http://localhost:11434/v1`。自定义本地服务可不填密钥。

输入一句文字并点击“发送”即可验证连接。程序发送角色提示词、最近六轮消息和当前输入；本轮成功后才加入对话历史，点击“清空当前对话”可重置。历史当前只保存在该窗口的内存中，关闭即清空。这个窗口继续保留为独立的文字调试入口；主语音窗口也会读取这里保存的模型设置。`llm.py` 负责配置与 HTTP 请求，`chat_worker.py` 负责后台请求，`llm_gui.py` 负责文字测试界面。

调用可能产生服务商费用；只有点击“发送”才请求模型。“保存设置与密钥”不会发起模型请求。无真实密钥的本地验证可运行 `.\.venv\Scripts\python.exe -m unittest -v test_llm.py`。

本机已用硅基流动 `deepseek-ai/DeepSeek-V4-Flash` 完成一次真实请求，返回了简短中文问候。密钥没有出现在命令、测试输出或本说明中。

## 图形界面

双击 `启动界面.cmd`。窗口中的“麦克风”可以选系统默认设备，也可以指定 Realtek 或其他输入设备；“刷新”会重新读取设备列表。“识别语言”默认是中文，需要时可改为自动识别或其他语言。

点击“开始录音”后说话，再点击“停止并识别”。录音最多 60 秒，文字显示在结果框中，可以一键复制。“试用示例”会读取目录里的中文示例音频，供你先检查模型是否工作。录音只在内存中处理，不会保存麦克风音频文件。

“开启唤醒监听”会一直读取麦克风，但只在 Silero VAD 检测到一段人声并判断说话结束后，才调用 SenseVoice 识别这一句。初始静音结束阈值为 0.8 秒，保留约 0.25 秒的前置声音。启动后显示“待唤醒”：说“爱莉”或设置中的识别别名（默认“爱丽、艾莉、艾丽”）会进入对话状态；接下来 30 秒内说的话会显示在结果框中。说“爱丽，帮我……”时，该句也会显示为“爱莉，帮我……”。单独叫名字只唤醒，不发送模型。带内容的唤醒句与后续每句有效讲话，在“唤醒后自动发送给模型”开启时，会去掉句首称呼后发送给模型。每轮回复结束后重新开始 30 秒倒计时，超时后返回待唤醒。原来的手动录音和示例识别仍可用于调试，它们不经过唤醒门控，也不发送模型。

界面中的“唤醒称呼”“识别别名”“对话保持”可修改，失去焦点或关闭窗口时保存到 `settings.json`，下次启动会读取。当前版本的 sherpa-onnx SenseVoice 调用没有通用提示词参数，所以别名校正发生在识别文字之后、对话状态判断之前，不会改变模型原始解码。只有句首的称呼会触发唤醒，避免正文中碰巧出现名字时误唤醒；不在别名列表中的错字不会自动猜测。可根据实际识别结果继续添加别名。

现在模型生成与语音播报期间仍保持麦克风监听，界面显示 `Listening / Thinking / Speaking` 状态。回复收到后按句分段交给 Qt TextToSpeech 播放；说话打断时会停止当前段并清空剩余段落。如果用户在模型生成期间说了新的一句，旧请求即使稍后返回也不会进入对话历史或播报。主语音窗口保存最近六轮成功对话用于续聊，关闭程序或点“清空对话”后清除。

你主要使用扬声器，因此默认选择“扬声器：说唤醒名后打断”：播报期间说“爱莉，等等”这样的完整短句，待 VAD 判定句尾并识别后，中断播报并处理新请求。扬声器模式把较长回复切成短段，段间留约 1.1 秒，让 VAD 有机会在静音处完成一段；检测到声音时下一段会等待识别完成。程序会过滤与当前回复相似的识别文字，也要求播报期间的打断句以唤醒称呼开头；这只是回声防护，**不是声学回声消除（AEC）**。环境、人声或音量较大的扬声器仍可能造成漏识别或误触发。耳机模式下可选择“检测到说话立即打断”，它在 VAD 发现语音开始时就停止播报；使用扬声器时不建议选此模式。“立即停止当前回复”按钮始终可在生成或播报时使用。当前是完整 LLM 回复后的分段 TTS，还不是模型 token 流式生成。持续监听由你在界面中手动开启，关闭窗口时会停止采集。

如果窗口没有打开，可在 PowerShell 中运行 `.\.venv\Scripts\python.exe .\gui.py` 查看错误。

## 命令行试用

在 PowerShell 中进入本目录：

```powershell
cd C:\CProj\Airi\Shimano\SenseVoice
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe .\recognize.py --file .\samples\zh.wav --language zh
.\.venv\Scripts\python.exe .\recognize.py --list-devices
.\.venv\Scripts\python.exe .\recognize.py --record --seconds 6 --device 1 --language zh
```

`--device 1` 在这台电脑上是默认的 Realtek 麦克风阵列。设备编号可能随插拔或系统设置改变，请以 `--list-devices` 的最新结果为准。命令行录音启动后立即说话，六秒后显示结果。模型在 CPU 上运行；第一次识别需要加载模型，可能比后续调用慢。

## 代码路线

界面入口是 `gui.py` 的 `MainWindow`。它负责麦克风选择、`Listening / Thinking / Speaking` 状态、打断、对话显示和分段 TTS；`RecognitionWorker` 处理单次录音，`ContinuousWorker` 处理持续监听，识别都在后台线程运行。`continuous.py` 的 `StreamingVad` 接受音频帧，返回已经说完的片段。`wake.py` 的 `ConversationGate` 接收每句识别文字，校正句首称呼并维护待唤醒/对话中的超时状态。`interaction.py` 拆分回复语句并过滤疑似播报回声。`chat_worker.py` 在后台发送模型请求；只有当前有效请求的成功回复才进入会话历史。

1. `record()`：以 16 kHz、单声道采集麦克风声音，得到浮点数数组。
2. `speech_spans()`：Silero VAD 找出数组中有人说话的位置，去掉较长的静音。
3. `recognize()`：SenseVoice 对每段语音解码，合并成文字。

`recognize.py` 的 VAD 和解码流程参考了 [Sakura 的 SenseVoice 插件](https://github.com/Rvosy/Sakura/tree/main/plugins/optional/sakura_asr_sensevoice)，其 MIT 许可文本保留在 `third_party/Sakura-LICENSE.txt`。这里使用相同版本的模型、词表和 VAD，但不会上传 Sakura 源码目录或程序包。模型权重、sherpa-onnx 与 VAD 各有自己的许可和来源，见项目根目录的 `THIRD_PARTY.md`。

`samples/zh.wav` 来自 [sherpa-onnx 的 SenseVoice 示例资源](https://huggingface.co/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tree/2365baeacb507f821a0c8120fcee3d484dba7a07/test_wavs)。它用于本地验证；发布或分享样本时应先核对其授权。

本机已验证：示例 WAV 识别为“开放时间早上9点至下午5点。”；Realtek 麦克风可以打开 16 kHz 输入流。真实讲话的识别效果还需你对着麦克风运行上面的录音命令检验。

图形界面也已验证示例识别、设备选择，以及 Realtek 麦克风的开始和停止录音。空白录音会提示“没有检测到人声”，并恢复按钮状态。

持续监听已用分帧示例音频验证：VAD 在句尾静音后输出一个片段，识别结果为“开放时间早上9点至下午5点。”；Realtek 麦克风的持续监听启动与停止也已验证。唤醒、模型请求、暂停与恢复采集的逻辑可运行 `.\.venv\Scripts\python.exe -m unittest -v test_voice_loop.py test_llm.py test_wake.py` 验证。Qt 的 Microsoft Yaoyao 中文发音人已实际播放测试短句，状态从 Speaking 返回 Ready。完整真实人声对话仍需对着麦克风验证，误触发和说话停顿长度也需边使用边调整。
