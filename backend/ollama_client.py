import requests
import json
import asyncio
from typing import List, Dict, Any, Optional

class OllamaClient:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.current_model = "danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth"
        self.session = requests.Session()
        self.timeout = 60
        
        # CRITICAL: Conversation context storage
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        
    def set_model(self, model_name: str):
        """Set the active model"""
        self.current_model = model_name
        
    def get_or_create_conversation(self, session_id: str = "default") -> List[Dict[str, str]]:
        """Get or create conversation history for a session"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        return self.conversation_history[session_id]
    
    def clear_conversation(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
    
    async def check_health(self) -> str:
        """Check if Ollama is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return "connected"
            else:
                return "error"
        except Exception as e:
            return f"offline: {str(e)}"
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("models", []):
                models.append({
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                })
            
            return models
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        session_id: str = "default"
    ) -> str:
        """Generate response from Ollama with conversation context"""
        model_to_use = model or self.current_model
        
        try:
            # Get conversation history
            messages = self.get_or_create_conversation(session_id)
            
            # Add system message if provided and not already present
            if system_prompt and (not messages or messages[0]["role"] != "system"):
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Use /api/chat endpoint for conversation context
            payload = {
                "model": model_to_use,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            print(f"DEBUG: Sending {len(messages)} messages to Ollama")
            print(f"DEBUG: Session ID: {session_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/chat",  # ← CRITICAL: Use /api/chat not /api/generate
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            assistant_response = result.get("message", {}).get("content", "").strip()
            
            # Add assistant response to conversation history
            messages.append({"role": "assistant", "content": assistant_response})
            
            print(f"DEBUG: Conversation now has {len(messages)} messages")
            
            return assistant_response
            
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Try using a smaller model."
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure it's running."
        except Exception as e:
            print(f"DEBUG: Error in generate_response: {e}")
            return f"Error: {str(e)}"
    
    async def generate_json_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """Generate JSON response from Ollama with conversation context"""
        json_system = "You are an AI assistant that responds only in valid JSON format. Do not include any text outside the JSON structure."
        
        if system_prompt:
            json_system += f" {system_prompt}"
        
        response_text = await self.generate_response(
            prompt=prompt,
            model=model,
            system_prompt=json_system,
            temperature=0.3,  # Lower temperature for more consistent JSON
            session_id=session_id
        )
        
        try:
            # Try to parse as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return error response
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_text
            }
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        try:
            models = asyncio.run(self.list_models())
            return any(model["name"] == model_name for model in models)
        except:
            return False
    
    def get_best_model_for_task(self, task_type: str) -> str:
        """Get the best available model for a specific task"""
        return "danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth"
    
    def get_conversation_summary(self, session_id: str = "default") -> Dict[str, Any]:
        """Get summary of conversation state"""
        messages = self.get_or_create_conversation(session_id)
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "has_system_prompt": len(messages) > 0 and messages[0]["role"] == "system",
            "last_user_message": next((msg["content"][:100] + "..." for msg in reversed(messages) if msg["role"] == "user"), None),
            "last_assistant_message": next((msg["content"][:100] + "..." for msg in reversed(messages) if msg["role"] == "assistant"), None)
        }