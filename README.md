# 豆包 Markdown 长文本 TTS

[![tests](https://github.com/compreader2023/doubao-md-tts/actions/workflows/test.yml/badge.svg)](https://github.com/compreader2023/doubao-md-tts/actions/workflows/test.yml)

把 Markdown 文档通过火山引擎/豆包 TTS 2.0 的异步长文本接口转换为音频。支持豆包声音复刻 2.0 音色，并允许你用中文自然语言描述整篇文章的情绪、语气和节奏。

适用于 macOS 和 Windows。程序只使用 Python 标准库，不需要手动安装第三方依赖；首次运行会在项目目录自动创建隔离的 `.venv` 虚拟环境。

## 功能

- 读取 `.md` 文档并清理标题符号、链接、列表标记和代码块；
- 使用豆包 TTS 2.0 异步长文本接口，单次最多 100,000 字符；
- 支持 `S_*` 开头的声音复刻 2.0 音色；
- 使用中文自然语言控制整篇文章的情绪；
- 自动提交任务、轮询进度并及时下载限时音频链接；
- 支持 MP3、WAV、OGG Opus 和 PCM；
- 保存任务 JSON 信息，超时后可凭任务 ID 继续查询；
- 密钥保存在本地独立文件中，不写进源代码。

> 本程序调用的是收费或按额度计费的云端 API。费用、授权和可用音色以你的火山引擎控制台为准。

## 一、准备豆包语音服务

使用前，你需要在[火山引擎豆包语音控制台](https://console.volcengine.com/speech/service/8)完成以下准备：

1. 开通豆包语音合成/异步长文本能力；
2. 如果使用自己的声音，完成声音复刻 2.0，并复制音色 ID（通常以 `S_` 开头）；
3. 创建 API Key，或者取得旧版 V3 的 `APP_ID` 与 `ACCESS_KEY`；
4. 确认账户有可用额度，并且相应模型服务已经开通。

官方资料：

- [异步长文本接口文档](https://www.volcengine.com/docs/6561/1829010)
- [声音复刻 2.0 最佳实践](https://www.volcengine.com/docs/6561/2298705)

## 二、下载程序

不会 Git 的用户：

1. [点击这里下载 v1.0.0 稳定版 ZIP](https://github.com/compreader2023/doubao-md-tts/archive/refs/tags/v1.0.0.zip)；
2. 解压 ZIP；
3. 把解压后的文件夹放到一个固定位置，例如：
   - macOS：`下载/doubao-md-tts`
   - Windows：`D:\Tools\doubao-md-tts`

也可以打开项目主页，点击绿色的 **Code** 按钮，再点击 **Download ZIP** 下载最新代码。

会使用 Git 的用户可以运行：

```bash
git clone https://github.com/compreader2023/doubao-md-tts.git
cd doubao-md-tts
```

## 三、安装 Python

需要 Python 3.10 或更高版本。建议使用目前受支持的 Python 3 版本。

### macOS

先打开“终端”：按 `Command + 空格`，输入“终端”并回车。检查是否已经安装：

```bash
python3 --version
```

如果显示 `Python 3.10` 或更高版本，可以直接进入下一节。

如果显示 `command not found` 或版本低于 3.10，推荐从 Python 官方网站安装：

1. 打开 [Python macOS 下载页](https://www.python.org/downloads/macos/)；
2. 下载适合 macOS 的最新版安装包；
3. 双击 `.pkg`，按提示完成安装；
4. 关闭并重新打开终端；
5. 再运行 `python3 --version` 检查。

熟悉 Homebrew 的用户也可以运行：

```bash
brew install python
```

### Windows 10 / Windows 11

先打开 PowerShell 或“命令提示符”。检查是否已经安装：

```powershell
py -3 --version
```

也可以尝试：

```powershell
python --version
```

如果没有 Python：

1. 打开 [Python Windows 下载页](https://www.python.org/downloads/windows/)；
2. 下载 64 位 Windows installer；
3. 启动安装程序；
4. **务必勾选 `Add python.exe to PATH`**；
5. 点击 `Install Now`；
6. 安装完成后关闭并重新打开 PowerShell；
7. 再运行 `py -3 --version` 检查。

如果输入 `python` 只打开 Microsoft Store，请改用 `py -3`，或在 Windows 设置的“应用执行别名”中关闭冲突的 Python 别名。

## 四、首次初始化

### macOS

在终端进入解压后的目录。路径中有空格时要加引号：

```bash
cd "$HOME/Downloads/doubao-md-tts"
chmod +x setup.sh tts.sh
./setup.sh
```

### Windows

在资源管理器中打开项目文件夹，在地址栏输入 `cmd` 并回车，然后运行：

```bat
setup.bat
```

也可以直接双击 `setup.bat`。脚本会创建 `.venv` 和配置文件 `TTSAPIKEY`。

## 五、填写密钥和克隆音色

`TTSAPIKEY` 是普通文本配置文件，但没有扩展名。

macOS 可运行：

```bash
open -e TTSAPIKEY
```

Windows 可运行：

```bat
notepad TTSAPIKEY
```

新版 API Key 的常用配置：

```text
TTS_API_KEY=在这里粘贴你的APIKey
APP_ID=
ACCESS_KEY=
VOICE_TYPE=S_你的克隆音色ID
RESOURCE_ID=
USER_ID=md-tts-user
```

使用旧版 V3 双凭证时：

```text
TTS_API_KEY=
APP_ID=你的AppID
ACCESS_KEY=你的AccessKey
VOICE_TYPE=S_你的克隆音色ID
RESOURCE_ID=
USER_ID=md-tts-user
```

`RESOURCE_ID` 通常可以留空，程序会自动选择：

| 音色类型 | 自动使用的 Resource ID |
| --- | --- |
| `S_*` 声音复刻 2.0 | `seed-icl-2.0` |
| 豆包 TTS 2.0 公版音色 | `seed-tts-2.0` |

如果控制台明确给出了其他 Resource ID，应以控制台为准。

## 六、转换 Markdown 文档

### macOS

```bash
./tts.sh "/完整路径/文章.md" \
  --emotion "像一位沉稳亲切的家长，诚恳、温暖、克制，重要结论稍作强调，整体节奏舒缓自然"
```

### Windows

```bat
tts.bat "D:\Documents\文章.md" --emotion "像一位沉稳亲切的家长，诚恳、温暖、克制，重要结论稍作强调，整体节奏舒缓自然"
```

如果不写 `--emotion`，程序会提示你现场输入整篇文章的情绪描述：

```bash
./tts.sh 文章.md
```

Windows 对应：

```bat
tts.bat 文章.md
```

默认在 Markdown 文档旁边生成：

- `文章.mp3`：音频文件；
- `文章.mp3.json`：任务状态、时间戳等服务端信息。

## 常用参数

指定输出位置：

```bash
./tts.sh 文章.md -e "温暖、真诚地朗读" -o 成品.mp3
```

改为 WAV、调整语速和音量：

```bash
./tts.sh 文章.md -e "清晰、有力量地朗读" --format wav --speech-rate -10 --loudness-rate 5
```

先检查 Markdown 清理结果，不调用 API、不产生费用：

```bash
./tts.sh 文章.md --dry-run
```

这会生成 `文章.tts.txt`，可以先打开检查实际会朗读哪些内容。

任务等待超时后继续查询：

```bash
./tts.sh --task-id 任务ID -o 成品.mp3
```

查看全部参数：

```bash
./tts.sh --help
```

Windows 把上述命令中的 `./tts.sh` 换成 `tts.bat` 即可。

## 情绪描述怎么写

情绪参数作用于整篇文章。尽量同时描述角色、情绪、强度、节奏和重点，例如：

- `像一位沉稳亲切的纪录片讲述者，温暖克制，节奏舒缓，关键数字略作强调。`
- `像给孩子讲睡前故事，柔和、有画面感，语速稍慢，结尾带一点希望。`
- `像发布重要消息，专业、自信、有感染力，但不要夸张。`
- `带着克制的悲伤和回忆感，停顿自然，不要哭腔过重。`

声音复刻 2.0 会结合文字语义进行演绎，不保证机械地完全服从每一个描述。训练声音样本本身的质量和情绪也会影响结果。

## 常见问题

### macOS 提示 `command not found: tts.sh`

当前目录的脚本需要带 `./`：

```bash
./tts.sh --help
```

### 提示没有执行权限

```bash
chmod +x setup.sh tts.sh
```

### Windows 提示“不是内部或外部命令”

先确认命令行当前位于程序目录，然后运行：

```bat
tts.bat --help
```

### `resource ID is mismatched with speaker related resource`

音色与资源类型不匹配。`S_*` 克隆音色通常应使用 `seed-icl-2.0`。建议先把 `RESOURCE_ID` 留空，让程序自动判断；若仍失败，请核对控制台中该音色所属的模型版本。

### `load grant: requested grant not found`

通常表示当前 API Key/AppID 没有开通对应资源，或密钥类型与鉴权方式不匹配。请在火山引擎控制台检查服务开通状态、项目、账户额度及 Resource ID。

### 任务一直显示“合成中”

异步长文本会排队，长文章可能需要较长时间。记下任务 ID，按 `Ctrl + C` 退出后，可稍后使用 `--task-id` 继续查询。

### Markdown 超过 100,000 字符

这是单次接口限制。请按章节拆成多个 Markdown 文件分别转换。

## 安全说明

- `TTSAPIKEY` 已加入 `.gitignore`，不会被正常的 Git 提交包含；
- 不要截图、分享或上传真实 API Key；
- 不要上传用于声音复刻的原始录音；
- 如果怀疑密钥泄露，请立即在控制台撤销并重新创建；
- 音频下载地址是限时链接，程序会在任务完成后立刻保存到本地。

## 开发与测试

项目没有运行时第三方依赖。开发者可以执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

Windows 激活命令为：

```bat
.venv\Scripts\activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

GitHub Actions 会在 macOS 和 Windows、Python 3.10 与 3.14 上运行测试。

## 许可证

[MIT License](LICENSE)

本项目不是火山引擎或字节跳动的官方项目。“豆包”“火山引擎”等名称归其各自权利人所有。
