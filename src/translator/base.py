from abc import ABC, abstractmethod
from typing import List, Dict
from tqdm import tqdm

class BaseTranslator(ABC):
    """
    Abstract base class for translation services
    """
    
    @abstractmethod
    def translate_single(self, text: str, target_language: str) -> str:
        """
        Translate a single piece of text
        
        Args:
            text (str): Text to be translated
            target_language (str): Target language code
        
        Returns:
            str: Translated text
        """
        pass

    def translate_batch(self, comments: Dict[int, str], target_language: str) -> Dict[int, str]:
        """
        Translate a batch of comments with progress bar
        
        Args:
            comments (Dict[int, str]): Dictionary of line numbers and comments
            target_language (str): Target language code
            
        Returns:
            Dict[int, str]: Dictionary of line numbers and translated comments
        """
        translated_comments = {}
        
        # Create progress bar
        with tqdm(total=len(comments), desc="Translating comments") as pbar:
            for line_num, comment in comments.items():
                translated = self.translate_single(comment, target_language)
                translated_comments[line_num] = translated
                pbar.update(1)
        
        return translated_comments
