import re
from typing import Optional
import string
from langdetect import detect, LangDetectException

class LanguageDetector:
    """
    Language detector for comments using langdetect library
    Currently supports: English (en), Chinese (zh), Japanese (jp)
    """

    # Language feature patterns used for auxiliary detection
    PATTERNS = {
        'zh': r'[\u4e00-\u9fff]',  # Chinese characters
        'jp': r'[\u3040-\u309f\u30a0-\u30ff]',  # Kana characters
    }

    # Language code mapping for langdetect
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
        Detect the language of the given text using "one drop rule"
        - If contains any Chinese characters -> Chinese
        - If contains any Japanese Kana (and no Chinese) -> Japanese 
        - If only contains English chars -> English

        Args:
            text (str): Text to detect

        Returns:
            str: Language code ('en', 'zh', 'jp') or None if unable to detect
        """
        # Remove common comment markers and whitespace
        text = re.sub(r'^[\/\*\s#]+|[\*\/\s]+$', '', text).strip()

        if not text:
            return None

        # Check Chinese first - one drop rule
        if re.search(LanguageDetector.PATTERNS['zh'], text):
            return 'zh'

        # Check Japanese Kana if no Chinese found
        if re.search(LanguageDetector.PATTERNS['jp'], text):
            return 'jp'

        # Only if no Chinese/Japanese chars found, check if pure English
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


#print(LanguageDetector.detect_language("のdocstring"))