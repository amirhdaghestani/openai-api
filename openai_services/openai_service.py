"""This module handles openai requests."""
import openai
import tiktoken

from configs.openai_config import OpenAIConfig
from logger.ve_logger import VeLogger


MODEL_PRICE_DICT = {
    "gpt-3.5-turbo": 0.002,
    "text-davinci-003": 0.02,
    "text-davinci-002": 0.02,
    "code-davinci-002": 0.02,
}


class OpenAIService:
    """This class handles openai requests."""

    # Initialize logger
    logger = VeLogger()

    def __init__(self, openai_config: OpenAIConfig=None) -> None:
        """Intializer method of the class
        
        Args:
            openai_config (OpenAIConfig): Neccessary configs for openai api.
            
        Returns:
            None
            
        """
        # Check Arguments
        if openai_config is None:
            self.logger.error("openai config is None.")
            raise ValueError("Provide openai_config when initializing class.")

        if openai_config.openai_api_key is None:
            self.logger.error("OpenAI API key is None.")
            raise ValueError(
                "Provide OpenAI API key when initializing class. You can set the " \
                "enviroment variable `OPENAI_API_KEY` to your OpeAI API key.")

        openai.api_key = openai_config.openai_api_key
        # self.model_list = self._get_models(openai.Model.list())

    def _get_models(self, model_list_raw: list):
        """Get models
        
        Args:
            model_list_raw (list): list of models obtained from openai.
        
        Returns:
            list: lists of openai models (completion, chat, similarity)

        """
        model_list = []
        for model_dict in model_list_raw.data:
            model_list.append(model_dict['id'])

        return model_list

    def _validate_model(self, model: str):
        """Validate model name"""
        if model in self.model_list:
            return True
        return False

    def _count_tokens(self, text: str, model: str):
        """Count tokens."""
        if self._validate_model(model):
            tokenizer = tiktoken.encoding_for_model(model)
            return len(tokenizer.encode(text))

    def completions(self, *args, **kwargs):
        """Completion models method"""
        return openai.Completion.create(*args, **kwargs)

    def chat_completions(self, *args, **kwargs):
        """Chat Completion models method"""
        return openai.ChatCompletion.create(*args, **kwargs)

    def embeddings(self, *args, **kwargs):
        """Embedding Completion models method"""
        return openai.Embedding.create(*args, **kwargs)

    def upload_files(self, *args, **kwargs):
        """Upload file.
        
        Args:
            file (any): File to upload.
            purpose (str): Purpose for file (Default: 'fine-tune').
        
        Returns:
            dict: Response from OpenAI

        """
        return openai.File.create(*args, **kwargs)

    def list_files(self):
        """Get the list of uploaded files.
        
        Args:
            None

        Returns:
            dict: Response from OpenAI
        
        """
        return openai.File.list()

    def fine_tunes(self, *args, **kwargs):
        """Finetune model via uploaded file.
        
        Args:
            None

        Returns:
            dict: Response from OpenAI
        
        """
        return openai.FineTune.create(*args, **kwargs)

    def retrieve_fine_tune(self, id: str):
        """Get the details of a finetuned model.
        
        Args:
            id (str): id of the fine-tuning process.

        Returns:
            dict: Response from OpenAI
        
        """
        return openai.FineTune.retrieve(id=id)

    def cancel_fine_tune(self, id: str):
        """Cancel a finetune process.
        
        Args:
            id (str): id of the fine-tuning process.

        Returns:
            dict: Response from OpenAI
        
        """
        return openai.FineTune.cancel(id=id)

    def list_fine_tunes(self):
        """Get the list of finetuned models.
        
        Args:
            None

        Returns:
            dict: Response from OpenAI
        
        """
        return openai.FineTune.list()
