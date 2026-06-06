# Lyrics Matcher

一个简单易用的歌词下载匹配工具。

## 功能特性

- 选择本地音频文件或文件夹
- 从网络搜索匹配的歌词
- 支持 Lrclib API
- 支持多种音频格式：MP3、FLAC、OGG、M4A、WAV、OPUS
- 歌词保存为 LRC 文件

## 安装

```bash
pip install -e .
```

## 使用

```bash
python -m lyrics_matcher
```

或直接运行：

```bash
lyrics-matcher
```

## 开发

```bash
pip install -e ".[dev]"
```

## 项目结构

```
lyrics_matcher/
├── src/
│   └── lyrics_matcher/
│       ├── __init__.py
│       ├── __main__.py
│       ├── audio.py       # 音频文件处理
│       ├── provider.py    # 歌词API提供者
│       └── gui.py         # GUI界面
├── tests/
├── pyproject.toml
└── README.md
```

##依赖

- Python >= 3.10
- mutagen - 音频标签处理
- requests - HTTP请求