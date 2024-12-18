import re
from typing import Optional
import string
from langdetect import detect, LangDetectException

class LanguageDetector:
    """
    Language detector for comments using langdetect library
    Currently supports: English (en), Chinese (zh), Japanese (jp)
    """

    # 用于辅助检测的语言特征模式
    PATTERNS = {
        'zh': r'[\u4e00-\u9fff]',  # 中文字符
        'jp': r'[\u3040-\u309f\u30a0-\u30ff]',  # 日文假名
    }

    # langdetect 语言代码映射
    LANG_MAP = {
        'zh-cn': 'zh',
        'zh-tw': 'zh',
        'ja': 'jp'
    }

    @staticmethod
    def is_english(text: str) -> bool:
        """Check if text contains only English characters, numbers, punctuation and whitespace"""
        text = text.strip()
        allowed_chars = set(string.ascii_letters + string.digits + string.punctuation + ' \n\t\r')
        return all(char in allowed_chars for char in text)

    @staticmethod
    def detect_language(text: str) -> Optional[str]:
        """
        Detect the language of the given text

        Args:
            text (str): Text to detect

        Returns:
            str: Language code ('en', 'zh', 'jp') or None if unable to detect
        """
        # 移除常见的注释标记和空白
        text = re.sub(r'^[\/\*\s#]+|[\*\/\s]+$', '', text).strip()

        if not text:
            return None

        # 首先尝试使用 langdetect
        try:
            detected = detect(text)
            # 映射语言代码
            if detected in LanguageDetector.LANG_MAP:
                return LanguageDetector.LANG_MAP[detected]
            elif detected == 'en':
                return 'en'
        except LangDetectException:
            pass  # 如果 langdetect 失败,继续使用备用方法

        # 备用检测方法
        # 检查中文
        if re.search(LanguageDetector.PATTERNS['zh'], text):
            return 'zh'

        # 检查日文假名
        if re.search(LanguageDetector.PATTERNS['jp'], text):
            return 'jp'

        # 检查英文
        if LanguageDetector.is_english(text):
            return 'en'

        return None

    @staticmethod
    def should_translate(text: str, source_language: Optional[str]) -> bool:
        """
        Determine if the text should be translated based on source language setting

        Args:
            text (str): Text to check
            source_language (str): Source language setting from config

        Returns:
            bool: True if should translate, False otherwise
        """
        if not source_language or source_language.lower() == 'any':
            return True

        detected_lang = LanguageDetector.detect_language(text)
        return detected_lang == source_language.lower()