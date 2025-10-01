import os
import json
from typing import Dict, List, Any

class MenuBotConfig:
    def __init__(self, config_file: str = "config/menubot_config.json"):
        self.config_file = config_file
        self.default_config = {
            "ollama": {
                "base_url": "http://localhost:11434",
                "timeout": 60,
                "models": {
                    "primary": "danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth",
                    "vision": "redule26/huihui_ai_qwen2.5-vl-7b-abliterated:latest",
                    "speed": "polaris:latest",
                    "fallback": "qwen3:30b"
                }
            },
            "generation_settings": {
                "stop": ["<|im_start|>", "<|im_end|>"],
                "temperature": 0.7,
                "min_p": 0.00,
                "repeat_penalty": 1.05,
                "top_k": 20,
                "top_p": 0.8,
                "max_tokens": 2000,
                "context_length": 1000000
            },
            "task_preferences": {
                "menu_generation": {
                    "model": "primary",
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                "action_execution": {
                    "model": "primary", 
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "vision_tasks": {
                    "model": "vision",
                    "temperature": 0.5,
                    "max_tokens": 1500
                },
                "quick_responses": {
                    "model": "speed",
                    "temperature": 0.5,
                    "max_tokens": 500
                }
            },
            "hardware": {
                "gpu_type": "auto",  # auto, cuda, rocm, cpu
                "vram_limit_gb": 24,
                "enable_gpu_layers": -1,  # -1 for auto, 0 for CPU only
                "batch_size": 512
            },
            "database": {
                "path": "database/menubot.db",
                "backup_enabled": True,
                "backup_interval_hours": 24
            },
            "ui": {
                "theme": "dark",
                "auto_save": True,
                "show_model_info": True,
                "default_role": "General User"
            },
            "media_processing": {
                "enable_image_processing": True,
                "enable_video_processing": False,
                "max_image_size_mb": 10,
                "supported_formats": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
                "video_formats": ["mp4", "avi", "mov", "webm"]
            },
            "security": {
                "api_key_required": False,
                "cors_enabled": True,
                "allowed_origins": ["*"],
                "rate_limit_enabled": False
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_config(self.default_config, config)
            else:
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config_to_save = config or self.config
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, path: str, default=None):
        """Get config value using dot notation (e.g., 'ollama.models.primary')"""
        keys = path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> bool:
        """Set config value using dot notation"""
        keys = path.split('.')
        config = self.config
        try:
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            config[keys[-1]] = value
            return self.save_config()
        except Exception as e:
            print(f"Error setting config: {e}")
            return False
    
    def get_model_settings(self, task_type: str = "default") -> Dict[str, Any]:
        """Get generation settings for specific task type"""
        base_settings = self.config["generation_settings"].copy()
        
        if task_type in self.config["task_preferences"]:
            task_settings = self.config["task_preferences"][task_type]
            base_settings.update(task_settings)
        
        return base_settings
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get the best model for a specific task"""
        model_key = self.get(f"task_preferences.{task_type}.model", "primary")
        return self.get(f"ollama.models.{model_key}", self.get("ollama.models.primary"))
    
    def detect_hardware(self) -> str:
        """Auto-detect hardware configuration"""
        # Check for NVIDIA GPU via nvidia-ml-py (lightweight) or environment
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                return "cuda"
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
    
        # Check for ROCm
        if os.path.exists("/opt/rocm") or "ROCM_PATH" in os.environ:
            return "rocm"
    
        return "cpu"
    
    def update_hardware_config(self):
        """Update hardware configuration based on detection"""
        if self.get("hardware.gpu_type") == "auto":
            detected = self.detect_hardware()
            self.set("hardware.gpu_type", detected)
            print(f"Detected hardware: {detected}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check if models exist (this would need Ollama integration)
        models = self.get("ollama.models", {})
        for model_type, model_name in models.items():
            if not model_name:
                issues.append(f"No model specified for {model_type}")
        
        # Check VRAM limits
        vram_limit = self.get("hardware.vram_limit_gb", 0)
        if vram_limit < 8:
            issues.append("VRAM limit is quite low - may affect performance")
        
        # Check file paths
        db_path = self.get("database.path")
        if db_path and not os.path.exists(os.path.dirname(db_path)):
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create database directory: {e}")
        
        return issues

# Global config instance
config = MenuBotConfig()

# Hardware detection on import
config.update_hardware_config()

# Convenience functions
def get_model_settings(task_type: str = "default") -> Dict[str, Any]:
    return config.get_model_settings(task_type)

def get_model_for_task(task_type: str) -> str:
    return config.get_model_for_task(task_type)

def get_ollama_url() -> str:
    return config.get("ollama.base_url", "http://localhost:11434")