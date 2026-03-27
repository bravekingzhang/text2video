# 一个文本转视频的工具

这个工具可以将一段文本转换为视频，并保存到指定的本地，初衷是想实现小说的可视化阅读功能。

效果图如下：

<img src="https://github.com/bravekingzhang/text2viedo/blob/main/demos/4301686560452_.pic.jpg" alt="效果图" style="width: 100%;" />

## 实现原理

- 将文本进行分段，现在没有想到好的办法，就是通过标点符号句号分段，分成一个个的句子
- 通过句子生成图片，生成声音，图片开源的有很多，本方案采用 stable-diffusion，语言转文字使用 edge-tts
- **通过大模型生成midjourney类的提示词，然后通过huggingface的模型生成图片**。
- 在通过 opencv 将图片合并为视频，目前输出 mp4 格式的视频，句子作为字母贴到视频内容的底部区域。
- 音频是一个有时间概念的东西，恰好可以通过音频控制一张画面的播放时长
- 在通过 ffmpeg 将音频合并到原始视频中。

最终，一个有画面，有字幕，有声音的视频就出现了，咱们实现了一个 `文本转视频`。

## Docker 一键启动

```shell
docker-compose up --build
```

## 本地开发

开发时，需要安装的环境是 `macOS` `python 3.10.12`，其他环境可能存在兼容性问题，需要安装 ffmpeg

```shell
ffmpeg -version
ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers
built with Apple clang version 14.0.3 (clang-1403.0.22.14.1)
```

pip install -r requirements.txt

## 支持生成绘图提示词来提高绘图质量

需要配置 LLM 的 api key，支持多个提供商切换：

### Moonshot（默认）

```shell
OPEN_AI_API_KEY="your moonshot api key"
OPEN_AI_BASE_URL="https://api.moonshot.cn/v1"
```

### OpenAI

```shell
LLM_PROVIDER="openai"
OPEN_AI_API_KEY="your openai api key"
```

### MiniMax

[MiniMax](https://www.minimax.io/) 提供高性能的 M2.7 大模型，支持 1M 上下文，适合生成高质量的绘图提示词。

```shell
LLM_PROVIDER="minimax"
MINIMAX_API_KEY="your minimax api key"
# 可选模型：MiniMax-M2.7（默认）、MiniMax-M2.7-highspeed（更快）
# LLM_MODEL="MiniMax-M2.7-highspeed"
```

> 提示：设置 `MINIMAX_API_KEY` 环境变量后即自动启用 MiniMax，无需额外设置 `LLM_PROVIDER`。

### 自定义提供商

任何兼容 OpenAI API 的服务都可以通过 `OPEN_AI_BASE_URL` 接入：

```shell
OPEN_AI_API_KEY="your api key"
OPEN_AI_BASE_URL="https://your-provider.com/v1"
LLM_MODEL="your-model-name"
```

## 生成 huggingface api key

token 申请地址：https://huggingface.co/settings/tokens

因为，该项目中使用了 huggingface 上的开源文生图模型生成图片，中文生成图片效果不大好，因此，本项目对中文进行了翻译，感谢有道，直接使用有道翻译，比较方便。翻译后，生成图的质量有一定的提高。

token 可以写入到 .env 文件里面
`API_TOKEN="your huggingface api token"`

### 如果使用的 pollinations-ai ，则不填写 token 也可以，这个模型是使用的 ChatGPT 的 Dalle-2 模型。

## 安装 ffmpeg

因为视频合成声音需要

## 开始使用

```python
python3.10 app.py
http://127.0.0.1:5001/
```

## 赞助

随意打赏，请备注 github 名
<img width="200" alt="image" src="https://github.com/bravekingzhang/react-ai-chat/assets/4476322/7c457992-a0bc-49a3-9bd6-f23b5f1a595e">

关注作者微信公众号，**老码沉思录**，与作者交流。
<img width="200" alt="image" src="https://raw.githubusercontent.com/bravekingzhang/pic_go/master/2024/03/29/1711677809867-40f26109-8ac4-45de-b8b2-cbf78ad09cff.png">

## License: MIT

本项目采用 MIT 许可证授权。
