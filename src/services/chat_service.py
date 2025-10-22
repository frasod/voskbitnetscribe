"""
Chat service - handles conversational interactions with BitNet.
"""

from typing import Optional, Callable
import requests
import json
from dataclasses import dataclass

from ..core.config import BitNetConfig


@dataclass
class ChatMessage:
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ChatResponse:
    """Response from chat interaction."""
    success: bool
    message: str
    error: Optional[str] = None


class ChatService:
    """
    Handles chat-based interaction with BitNet.
    Maintains conversation history.
    """
    
    def __init__(self, config: BitNetConfig):
        self._config = config
        self._history: list[ChatMessage] = []
        self._is_cancelled = False
    
    def send_message(
        self,
        message: str,
        callback_status: Optional[Callable[[str], None]] = None
    ) -> ChatResponse:
        """
        Send a chat message and get response.
        
        Args:
            message: User message to send
            callback_status: Optional status update callback
            
        Returns:
            ChatResponse with success status and message/error
        """
        if not message.strip():
            return ChatResponse(success=False, message="", error="Empty message")
        
        # Add user message to history
        self._history.append(ChatMessage(role="user", content=message))
        
        try:
            if callback_status:
                callback_status("Sending message...")
            
            response = self._call_api(message)
            
            if self._is_cancelled:
                self._is_cancelled = False
                return ChatResponse(success=False, message="", error="Cancelled by user")
            
            if response.success:
                # Add assistant response to history
                self._history.append(ChatMessage(role="assistant", content=response.message))
            
            return response
            
        except Exception as e:
            error_msg = f"Chat error: {str(e)}"
            return ChatResponse(success=False, message="", error=error_msg)
    
    def _call_api(self, message: str) -> ChatResponse:
        """Call BitNet API with chat message."""
        # Build context from conversation history
        context = self._build_context()
        
        # Construct prompt
        prompt = f"{context}\n\nUser: {message}\nAssistant:"
        
        payload = {
            "prompt": prompt,
            "n_predict": self._config.max_tokens,
            "temperature": self._config.temperature,
            "repeat_penalty": self._config.repeat_penalty,
            "repeat_last_n": self._config.repeat_last_n,
            "top_p": self._config.top_p,
            "top_k": self._config.top_k,
            "stop": ["\nUser:", "\n\n", "\nYou:", "\nQuestion:"],
            "stream": False
        }
        
        try:
            response = requests.post(
                self._config.endpoint_url,
                json=payload,
                timeout=self._config.timeout_seconds
            )
            
            if response.status_code != 200:
                return ChatResponse(
                    success=False,
                    message="",
                    error=f"API returned status {response.status_code}"
                )
            
            # Parse response
            result = self._parse_response(response.json())
            return ChatResponse(success=True, message=result)
            
        except requests.exceptions.Timeout:
            return ChatResponse(success=False, message="", error="Request timed out")
        except requests.exceptions.RequestException as e:
            return ChatResponse(success=False, message="", error=f"Network error: {str(e)}")
        except json.JSONDecodeError:
            return ChatResponse(success=False, message="", error="Invalid JSON response")
    
    def _build_context(self) -> str:
        """Build conversation context from history."""
        if not self._history:
            return "You are a helpful AI assistant. Respond concisely and accurately."
        
        # Include last N messages for context (prevent token overflow)
        max_history = 10
        recent = self._history[-max_history:] if len(self._history) > max_history else self._history
        
        lines = ["Conversation history:"]
        for msg in recent:
            role = msg.role.capitalize()
            lines.append(f"{role}: {msg.content}")
        
        return "\n".join(lines)
    
    def _parse_response(self, json_data: dict) -> str:
        """Parse API response to extract text."""
        # Try common response formats
        if "response" in json_data:
            return str(json_data["response"]).strip()
        if "text" in json_data:
            return str(json_data["text"]).strip()
        if "content" in json_data:
            return str(json_data["content"]).strip()
        if "completion" in json_data:
            return str(json_data["completion"]).strip()
        if "generated_text" in json_data:
            return str(json_data["generated_text"]).strip()
        
        # Fallback: return entire response as string
        return str(json_data)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history.clear()
    
    def get_history(self) -> list[ChatMessage]:
        """Get conversation history."""
        return self._history.copy()
    
    def cancel(self) -> None:
        """Cancel ongoing request."""
        self._is_cancelled = True
