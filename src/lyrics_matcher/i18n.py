"""Internationalization support for Lyrics Matcher."""

from typing import Dict

LANGUAGES = {
    "zh_CN": "简体中文",
    "en": "English",
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh_CN": {
        # Window titles
        "app_title": "歌词匹配器 v0.3",
        "ready_status": "就绪 - 请选择文件或文件夹开始",

        # Menu
        "menu_file": "文件",
        "menu_language": "语言",
        "menu_help": "帮助",
        "menu_exit": "退出",
        "menu_about": "关于",

        # Buttons
        "btn_select_files": "选择文件",
        "btn_select_folder": "选择文件夹",
        "btn_search": "搜索歌词",
        "btn_clear": "清除",
        "btn_select_all": "全选",
        "btn_deselect_all": "取消全选",
        "btn_invert_selection": "反选",
        "btn_save_selected": "保存选中",

        # Labels
        "label_files": "已选音频文件：",
        "label_results": "搜索结果 (Ctrl+点击多选)",
        "label_preview": "歌词预览 (双击保存)",
        "label_format": "格式",
        "label_selection": "选择",

        # Status messages
        "status_loaded": "已加载 {count} 个文件",
        "status_searching": "正在搜索...",
        "status_searching_progress": "搜索中... ({current}/{total})",
        "status_found": "找到 {count} 个歌词选项",
        "status_no_files": "未选择文件",
        "status_no_selection": "未选择歌词 - 使用 Ctrl+点击 或 全选",
        "status_saved": "已保存 {count} 个歌词文件",
        "status_cleared": "已清除",

        # Formats
        "format_lrc": "LRC",
        "format_enhanced": "逐字",
        "format_srt": "SRT",
        "format_ass": "ASS",

        # Dialogs
        "dialog_select_audio": "选择音频文件",
        "dialog_select_folder": "选择文件夹",
        "dialog_about_title": "关于歌词匹配器",
        "dialog_about_text": "歌词匹配器 v0.3\n\n一个简单易用的歌词下载匹配工具\n\n支持多平台歌词搜索、多种输出格式",
    },
    "en": {
        # Window titles
        "app_title": "Lyrics Matcher v0.3",
        "ready_status": "Ready - Select files or folder to begin",

        # Menu
        "menu_file": "File",
        "menu_language": "Language",
        "menu_help": "Help",
        "menu_exit": "Exit",
        "menu_about": "About",

        # Buttons
        "btn_select_files": "Select Files",
        "btn_select_folder": "Select Folder",
        "btn_search": "Search Lyrics",
        "btn_clear": "Clear",
        "btn_select_all": "Select All",
        "btn_deselect_all": "Deselect All",
        "btn_invert_selection": "Invert Selection",
        "btn_save_selected": "Save Selected",

        # Labels
        "label_files": "Selected Audio Files:",
        "label_results": "Search Results (Ctrl+Click for multi-select)",
        "label_preview": "Lyrics Preview (Double-click to save)",
        "label_format": "Format",
        "label_selection": "Selection",

        # Status messages
        "status_loaded": "Loaded {count} files",
        "status_searching": "Searching...",
        "status_searching_progress": "Searching... ({current}/{total})",
        "status_found": "Found {count} lyrics options",
        "status_no_files": "No files selected",
        "status_no_selection": "No lyrics selected - use Ctrl+Click or Select All",
        "status_saved": "Saved {count} lyrics files",
        "status_cleared": "Cleared",

        # Formats
        "format_lrc": "LRC",
        "format_enhanced": "Enhanced",
        "format_srt": "SRT",
        "format_ass": "ASS",

        # Dialogs
        "dialog_select_audio": "Select Audio Files",
        "dialog_select_folder": "Select Folder",
        "dialog_about_title": "About Lyrics Matcher",
        "dialog_about_text": "Lyrics Matcher v0.3\n\nA simple and user-friendly lyrics download and matching tool\n\nSupports multi-platform lyrics search and multiple output formats",
    },
}


class I18n:
    """Internationalization manager."""

    def __init__(self, language: str = "zh_CN"):
        self.language = language
        self._translations = TRANSLATIONS.get(language, TRANSLATIONS["zh_CN"])

    def t(self, key: str, **kwargs) -> str:
        """Translate a key with optional formatting."""
        text = self._translations.get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text

    def set_language(self, language: str):
        """Change the current language."""
        if language in TRANSLATIONS:
            self.language = language
            self._translations = TRANSLATIONS[language]
            return True
        return False

    def get_language(self) -> str:
        """Get the current language code."""
        return self.language


i18n = I18n("zh_CN")


def set_language(lang: str) -> None:
    """Set the global language."""
    i18n.set_language(lang)


def t(key: str, **kwargs) -> str:
    """Translate a key using the global i18n instance."""
    return i18n.t(key, **kwargs)