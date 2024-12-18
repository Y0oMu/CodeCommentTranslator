import yaml
from openai import OpenAI
from .base import BaseTranslator
from .prompt_template import PromptTemplate

class OpenAITranslator(BaseTranslator):
    """
    Translator implementation using OpenAI's API
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize OpenAI Translator
        
        Args:
            config_path (str): Path to configuration file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config file: {e}")

        openai_config = config.get('openai', {})
        self.api_key = openai_config.get('api_key')
        self.base_url = openai_config.get('base_url')
        self.model_name = openai_config.get('model_name', 'gpt-4o-mini')

        if not self.api_key:
            raise ValueError("OpenAI API key not found in config file")

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("OpenAI library is not installed. Please install it using 'pip install openai'")
    
    def translate_single(self, text: str, target_language: str) -> str:
        """
        Translate text using OpenAI's API
        
        Args:
            text (str): Text to be translated
            target_language (str): Target language code
        
        Returns:
            str: Translated text
        """
        try:
            # Clean comment markers before translation
            clean_text = PromptTemplate.clean_comment_markers(text)
            
            # Get translation prompt
            prompt = PromptTemplate.get_openai_prompt(target_language)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": "Instruction:Please only output the translated results, do not output any other content \n Code comments that need to be translated:"+clean_text}
                ]
            )
            
            translated_text = response.choices[0].message.content.strip()
            #print(translated_text)
            # Restore comment format
            return PromptTemplate.restore_comment_format(text, translated_text)
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original text if translation fails
