

class PromptTemplate:
    """
    Manages translation prompt templates for different translation engines
    """
    
    @staticmethod
    def get_openai_prompt(target_language: str) -> dict:
        """
        Get OpenAI translation prompt
        
        Args:
            target_language (str): Target language for translation
            
        Returns:
            dict: System and user message templates
        """
        return {
            "system": (
                f"You are a code comment translator. Translate the following code comments to {target_language}. "
                "Maintain the same meaning and technical accuracy. "
                "Return only the translated text without any explanations or additional formatting."
            ),
            "user": "Code comments that need to be translated: {text} "  # Will be formatted with the actual comment text
        }

    @staticmethod
    def clean_comment_markers(text: str) -> str:
        """
        Remove comment markers from text before translation
        
        Args:
            text (str): Original comment text
            
        Returns:
            str: Clean text without comment markers
        """
        # Remove single-line comment markers
        text = text.replace('#', '').replace('//', '')
        
        # Remove multi-line comment markers
        text = text.replace('"""', '').replace("'''", '')
        text = text.replace('/*', '').replace('*/', '')
        
        # Clean up any remaining whitespace
        text = text.strip()
        
        return text

    @staticmethod
    def restore_comment_format(original: str, translated: str) -> str:
        """
        Restore comment markers and format after translation
        
        Args:
            original (str): Original comment with markers
            translated (str): Translated text without markers
            
        Returns:
            str: Translated text with restored comment markers
        """
        # Detect original comment style
        if original.startswith('#'):
            return f"# {translated}"
        elif original.startswith('//'):
            return f"// {translated}"
        elif original.startswith('"""') or original.startswith("'''"):
            marker = '"""' if original.startswith('"""') else "'''"
            return f"{marker}\n{translated}\n{marker}"
        elif original.startswith('/*'):
            return f"/*\n{translated}\n*/"
        
        return translated  # Default case
