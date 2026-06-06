# Lyrics Matcher

一个简单易用的歌词下载匹配工具，支持多线程搜索和多平台歌词源。

## 功能特性

- **多线程搜索** - 并发搜索多个歌词源，速度更快
- **多平台歌词源** - 支持 LRCLIB、网易云音乐、QQ音乐
- **多种输出格式** - LRC、逐字歌词、SRT、ASS
- **音频标签写入** - 直接将歌词写入音频文件的元数据标签
- **批量处理** - 支持选择文件夹批量匹配歌词
- **支持多种音频格式** - MP3、FLAC、OGG、M4A、WAV、OPUS

## 支持的歌词格式

| 格式 | 说明 |
|------|------|
| LRC | 标准同步歌词 |
| Enhanced LRC | 逐字歌词（卡拉OK样式） |
| SRT | 字幕格式 |
| ASS | 高级字幕格式（带样式） |

## 支持的音频格式

- MP3 (ID3v2)
- FLAC
- OGG Vorbis/Speex/Opus
- M4A/AAC
- WAV
- WMA

## 安装

```bash
pip install -e .
```

## 使用

```bash
python -m lyrics_matcher
```

### GUI 使用说明

1. 点击「Select Files」选择音频文件，或「Select Folder」选择文件夹
2. 点击「Search Lyrics」搜索歌词（自动从多个平台搜索）
3. 在搜索结果中选择一个歌词
4. 选择输出格式（LRC/Enhanced/SRT/ASS）
5. 点击「Save to File」保存到文件，或「Write to Tag」写入音频标签

## 项目结构

```
lyrics_matcher/
├── src/lyrics_matcher/
│   ├── __init__.py
│   ├── __main__.py
│   ├── audio.py       # 音频文件处理（标签读写、格式转换）
│   ├── provider.py # 歌词API提供者（多平台、多线程）
│   └── gui.py # GUI界面
├── tests/
│   └── test_lyrics_matcher.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 依赖

- Python >= 3.10
- mutagen - 音频标签处理
- requests - HTTP请求

## API 源

- [LRCLIB](https://lrclib.net/) - 开源歌词数据库
- [网易云音乐](https://music.163.com/) - 通过非官方API
- [QQ音乐](https://y.qq.com/) - 通过非官方API

## License

GPL-3.0