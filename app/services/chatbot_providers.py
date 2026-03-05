"""
Multi-Provider Chatbot System
Supports multiple AI providers with configurable models and robust error handling
"""
import os
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Base class for AI providers"""
    
    @abstractmethod
    def chat(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        """Send chat messages to the provider"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI Provider (GPT-4, GPT-3.5, etc.)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv('OPENAI_API_KEY', '')).strip()
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').strip()
    
    def is_configured(self, api_key: Optional[str] = None) -> bool:
        return bool(api_key or self.api_key)
    
    def get_available_models(self) -> List[str]:
        return [
            'gpt-4-turbo-preview',
            'gpt-4',
            'gpt-4-32k',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k',
            'gpt-4o',
            'gpt-4o-mini'
        ]
    
    def chat(self, messages: List[Dict], model: str = 'gpt-3.5-turbo', api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> Dict:
        # Use provided API key or fall back to instance key
        use_api_key = api_key or self.api_key
        use_base_url = base_url or self.base_url
        
        if not use_api_key:
            return {
                'success': False,
                'error': 'OpenAI API key not configured',
                'provider': 'openai'
            }
        
        try:
            import openai
            client = openai.OpenAI(api_key=use_api_key, base_url=use_base_url)
            
            # Validate messages
            if not messages or not isinstance(messages, list):
                return {
                    'success': False,
                    'error': 'Invalid messages format',
                    'provider': 'openai'
                }
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000)
            )
            
            if not response.choices or len(response.choices) == 0:
                return {
                    'success': False,
                    'error': 'No response from OpenAI',
                    'provider': 'openai'
                }
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'model': model,
                'provider': 'openai',
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': 'OpenAI library not installed. Install with: pip install openai',
                'provider': 'openai'
            }
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'openai'
            }


class AnthropicProvider(AIProvider):
    """Anthropic Provider (Claude)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv('ANTHROPIC_API_KEY', '')).strip()
    
    def is_configured(self, api_key: Optional[str] = None) -> bool:
        return bool(api_key or self.api_key)
    
    def get_available_models(self) -> List[str]:
        return [
            'claude-3-5-sonnet-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-3-5-haiku-20241022'
        ]
    
    def chat(self, messages: List[Dict], model: str = 'claude-3-sonnet-20240229', api_key: Optional[str] = None, **kwargs) -> Dict:
        # Use provided API key or fall back to instance key
        use_api_key = api_key or self.api_key
        
        if not use_api_key:
            return {
                'success': False,
                'error': 'Anthropic API key not configured',
                'provider': 'anthropic'
            }
        
        try:
            import anthropic
            
            # Validate messages
            if not messages or not isinstance(messages, list):
                return {
                    'success': False,
                    'error': 'Invalid messages format',
                    'provider': 'anthropic'
                }
            
            client = anthropic.Anthropic(api_key=use_api_key)
            
            # Convert messages format for Anthropic
            system_message = None
            chat_messages = []
            for msg in messages:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    continue
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    chat_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            if not chat_messages:
                return {
                    'success': False,
                    'error': 'No valid messages to send',
                    'provider': 'anthropic'
                }
            
            response = client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7),
                system=system_message,
                messages=chat_messages
            )
            
            if not response.content or len(response.content) == 0:
                return {
                    'success': False,
                    'error': 'No response from Anthropic',
                    'provider': 'anthropic'
                }
            
            return {
                'success': True,
                'content': response.content[0].text,
                'model': model,
                'provider': 'anthropic',
                'usage': {
                    'input_tokens': response.usage.input_tokens if response.usage else 0,
                    'output_tokens': response.usage.output_tokens if response.usage else 0
                }
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Anthropic library not installed. Install with: pip install anthropic',
                'provider': 'anthropic'
            }
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'anthropic'
            }


class GoogleProvider(AIProvider):
    """Google Provider (Gemini)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv('GOOGLE_API_KEY', '')).strip()
    
    def is_configured(self, api_key: Optional[str] = None) -> bool:
        return bool(api_key or self.api_key)
    
    def get_available_models(self) -> List[str]:
        return [
            'gemini-pro',
            'gemini-pro-vision',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-ultra'
        ]
    
    def chat(self, messages: List[Dict], model: str = 'gemini-pro', api_key: Optional[str] = None, **kwargs) -> Dict:
        # Use provided API key or fall back to instance key
        use_api_key = api_key or self.api_key
        
        if not use_api_key:
            return {
                'success': False,
                'error': 'Google API key not configured',
                'provider': 'google'
            }
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=use_api_key)
            
            # Validate messages
            if not messages or not isinstance(messages, list):
                return {
                    'success': False,
                    'error': 'Invalid messages format',
                    'provider': 'google'
                }
            
            # Convert messages format for Google
            chat_history = []
            for msg in messages:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    continue
                if msg['role'] != 'system':
                    chat_history.append({
                        'role': 'user' if msg['role'] == 'user' else 'model',
                        'parts': [str(msg['content'])]
                    })
            
            if not chat_history:
                return {
                    'success': False,
                    'error': 'No valid messages to send',
                    'provider': 'google'
                }
            
            model_instance = genai.GenerativeModel(model)
            chat = model_instance.start_chat(history=chat_history[:-1] if len(chat_history) > 1 else [])
            
            last_message = chat_history[-1]['parts'][0] if chat_history else messages[-1].get('content', '')
            response = chat.send_message(last_message)
            
            if not response or not response.text:
                return {
                    'success': False,
                    'error': 'No response from Google',
                    'provider': 'google'
                }
            
            return {
                'success': True,
                'content': response.text,
                'model': model,
                'provider': 'google'
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Google Generative AI library not installed. Install with: pip install google-generativeai',
                'provider': 'google'
            }
        except Exception as e:
            logger.error(f"Google chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'google'
            }


class CohereProvider(AIProvider):
    """Cohere Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv('COHERE_API_KEY', '')).strip()
    
    def is_configured(self, api_key: Optional[str] = None) -> bool:
        return bool(api_key or self.api_key)
    
    def get_available_models(self) -> List[str]:
        return [
            'command',
            'command-light',
            'command-nightly',
            'command-light-nightly'
        ]
    
    def chat(self, messages: List[Dict], model: str = 'command', api_key: Optional[str] = None, **kwargs) -> Dict:
        # Use provided API key or fall back to instance key
        use_api_key = api_key or self.api_key
        
        if not use_api_key:
            return {
                'success': False,
                'error': 'Cohere API key not configured',
                'provider': 'cohere'
            }
        
        try:
            import cohere
            
            # Validate messages
            if not messages or not isinstance(messages, list):
                return {
                    'success': False,
                    'error': 'Invalid messages format',
                    'provider': 'cohere'
                }
            
            client = cohere.Client(api_key=use_api_key)
            
            # Get the last user message
            user_message = None
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    user_message = str(msg.get('content', ''))
                    break
            
            if not user_message:
                return {
                    'success': False,
                    'error': 'No user message found',
                    'provider': 'cohere'
                }
            
            response = client.chat(
                model=model,
                message=user_message,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000)
            )
            
            if not response or not response.text:
                return {
                    'success': False,
                    'error': 'No response from Cohere',
                    'provider': 'cohere'
                }
            
            return {
                'success': True,
                'content': response.text,
                'model': model,
                'provider': 'cohere'
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Cohere library not installed. Install with: pip install cohere',
                'provider': 'cohere'
            }
        except Exception as e:
            logger.error(f"Cohere chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'cohere'
            }


class HuggingFaceProvider(AIProvider):
    """HuggingFace Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv('HUGGINGFACE_API_KEY', '')).strip()
    
    def is_configured(self, api_key: Optional[str] = None) -> bool:
        return bool(api_key or self.api_key)
    
    def get_available_models(self) -> List[str]:
        return [
            'meta-llama/Llama-2-70b-chat-hf',
            'mistralai/Mistral-7B-Instruct-v0.1',
            'tiiuae/falcon-7b-instruct',
            'microsoft/DialoGPT-large'
        ]
    
    def chat(self, messages: List[Dict], model: str, api_key: Optional[str] = None, **kwargs) -> Dict:
        # Use provided API key or fall back to instance key
        use_api_key = api_key or self.api_key
        
        if not use_api_key:
            return {
                'success': False,
                'error': 'HuggingFace API key not configured',
                'provider': 'huggingface'
            }
        
        try:
            import requests
            
            # Validate messages
            if not messages or not isinstance(messages, list):
                return {
                    'success': False,
                    'error': 'Invalid messages format',
                    'provider': 'huggingface'
                }
            
            # Get the last user message
            user_message = None
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    user_message = str(msg.get('content', ''))
                    break
            
            if not user_message:
                return {
                    'success': False,
                    'error': 'No user message found',
                    'provider': 'huggingface'
                }
            
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {use_api_key}"}
            
            payload = {
                "inputs": user_message,
                "parameters": {
                    "temperature": kwargs.get('temperature', 0.7),
                    "max_new_tokens": kwargs.get('max_tokens', 1000)
                }
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get('generated_text', '')
            elif isinstance(result, dict):
                content = result.get('generated_text', str(result))
            else:
                content = str(result)
            
            if not content:
                return {
                    'success': False,
                    'error': 'No response from HuggingFace',
                    'provider': 'huggingface'
                }
            
            return {
                'success': True,
                'content': content,
                'model': model,
                'provider': 'huggingface'
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Requests library not installed. Install with: pip install requests',
                'provider': 'huggingface'
            }
        except Exception as e:
            logger.error(f"HuggingFace chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'huggingface'
            }


class ChatbotManager:
    """Manages multiple AI providers"""
    
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'google': GoogleProvider(),
            'cohere': CohereProvider(),
            'huggingface': HuggingFaceProvider()
        }
    
    def get_available_providers(self, user_api_keys: Optional[Dict] = None) -> List[Dict]:
        """Get list of available and configured providers"""
        available = []
        for name, provider in self.providers.items():
            try:
                # Check if user has API key for this provider
                user_key = user_api_keys.get(name, {}).get('api_key') if user_api_keys else None
                is_configured = provider.is_configured(user_key) if user_key else provider.is_configured()
                
                available.append({
                    'name': name,
                    'display_name': name.capitalize(),
                    'configured': is_configured,
                    'models': provider.get_available_models() if is_configured else []
                })
            except Exception as e:
                logger.error(f"Error getting provider info for {name}: {e}")
                available.append({
                    'name': name,
                    'display_name': name.capitalize(),
                    'configured': False,
                    'models': []
                })
        return available
    
    def chat(self, provider_name: str, messages: List[Dict], model: str, user_api_keys: Optional[Dict] = None, **kwargs) -> Dict:
        """Send chat message using specified provider"""
        if provider_name not in self.providers:
            return {
                'success': False,
                'error': f'Provider {provider_name} not found'
            }
        
        provider = self.providers[provider_name]
        
        # Get user API key if available
        user_key_data = user_api_keys.get(provider_name, {}) if user_api_keys else {}
        user_api_key = user_key_data.get('api_key')
        user_base_url = user_key_data.get('base_url')
        
        # Check if configured (with user key or default)
        is_configured = provider.is_configured(user_api_key) if user_api_key else provider.is_configured()
        
        if not is_configured:
            return {
                'success': False,
                'error': f'Provider {provider_name} is not configured. Please enter your API key.'
            }
        
        # Pass user API key to provider
        if user_api_key:
            if provider_name == 'openai':
                return provider.chat(messages, model, api_key=user_api_key, base_url=user_base_url, **kwargs)
            else:
                return provider.chat(messages, model, api_key=user_api_key, **kwargs)
        else:
            return provider.chat(messages, model, **kwargs)
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider"""
        if provider_name not in self.providers:
            return []
        
        provider = self.providers[provider_name]
        if not provider.is_configured():
            return []
        
        try:
            return provider.get_available_models()
        except Exception as e:
            logger.error(f"Error getting models for {provider_name}: {e}")
            return []
