import json
from typing import List, Dict, Any, Optional
from ollama_client import OllamaClient
from datetime import datetime
import os

def debug_log(message, data=None):
    """Write debug info to a file that you can easily check"""
    debug_file = "debug_log.txt"
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    with open(debug_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
        if data:
            f.write(f"    Data: {json.dumps(data, indent=2, default=str)}\n")
        f.write("-" * 50 + "\n")

class MenuGenerator:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        
    async def generate_menu(
        self, 
        role: str, 
        context: str, 
        current_node_content: str = "",
        node_title: str = "",
        parent_content: str = "",
        node_type: str = "menu",
        completed_actions: List[str] = None,
        previous_actions: List[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate context-aware menu options based on specific node content"""
        
        if completed_actions is None:
            completed_actions = []
        if previous_actions is None:
            previous_actions = []

        print(f"DEBUG: Completed actions received: {completed_actions}")
        print(f"DEBUG: Current node title: {node_title}")
            
        # Build the prompt for node-specific menu generation
        system_prompt = f"""You are MenuBot, a workflow assistant specializing in {role} tasks.

LOCATION CONTEXT: You are operating in the UK/British market. Use British English, GBP currency, UK demographics, British cultural references, and UK business practices. Avoid US-centric assumptions.

Your job is to generate 3-5 practical next actions based on the SPECIFIC CONTENT of the current node, not generic actions.

CRITICAL RULES:
1. Read the current node's content carefully and build on what it contains
2. NEVER suggest actions that have already been completed (listed in completed_actions)
3. Generate actions that logically follow from the current node's specific results
4. Focus on advancing the workflow, not repeating previous work

Return ONLY a JSON array in this exact format:
[
  {{
    "title": "Action Title",
    "prompt": "Detailed prompt for executing this action based on current node content",
    "tools": ["tool1", "tool2"],
    "alt": "Alternative description",
    "icon": "📋"
  }}
]

Generate actions that:
- Build directly on the current node's specific content
- Advance the workflow to the next logical phase
- Are contextually relevant to what was just discovered/created
- Avoid repeating any completed actions"""

        # Build contextual prompt based on current node
        if current_node_content and len(current_node_content) > 50:
            user_prompt = f"""Current Node: "{node_title}"
Current Node Content: {current_node_content[:1000]}...

Role: {role}
Overall Context: {context}

Already Completed Actions (DO NOT repeat these): {', '.join(completed_actions)}

Based on the SPECIFIC CONTENT of the current node above, generate 3-5 logical next actions that build on what this node contains. Focus on what the current node discovered or created, and suggest actions that advance from these specific findings."""
        else:
            # Fallback for start nodes or nodes without content
            user_prompt = f"""Role: {role}
Context: {context}
Current Situation: {node_title}

Already Completed Actions (DO NOT repeat these): {', '.join(completed_actions)}

Generate 3-5 logical next actions to begin or advance this workflow. Avoid repeating any completed actions."""

        try:
            # Use the primary model for menu generation
            response = await self.ollama.generate_json_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.ollama.current_model
            )
            
            # Handle potential parsing errors
            if "error" in response:
                return self._generate_fallback_menu(role, context, completed_actions)
            
            # Validate response is a list
            if isinstance(response, list):
                validated_menu = self._validate_menu_items(response)
                # Filter out any items that match completed actions
                filtered_menu = self._filter_completed_actions(validated_menu, completed_actions)
                return filtered_menu
            else:
                return self._generate_fallback_menu(role, context, completed_actions)
                
        except Exception as e:
            print(f"Menu generation error: {e}")
            return self._generate_fallback_menu(role, context, completed_actions)
    
    def _filter_completed_actions(self, menu_items: List[Dict[str, Any]], completed_actions: List[str]) -> List[Dict[str, Any]]:
        """Filter out menu items that match already completed actions"""
        if not completed_actions:
            return menu_items
            
        filtered_items = []
        for item in menu_items:
            item_title = item.get("title", "").lower()
            
            # Check if this action is too similar to completed actions
            is_duplicate = False
            for completed in completed_actions:
                completed_lower = completed.lower()
                # Check for exact matches or very similar titles
                if (item_title == completed_lower or 
                    item_title in completed_lower or 
                    completed_lower in item_title):
                    is_duplicate = True
                    break
                    
                # Check for semantic duplicates (research, analyze, etc.)
                duplicate_keywords = [
                    ("research", "research"), ("analyze", "analyz"), 
                    ("identify", "identif"), ("develop", "develop"),
                    ("create", "creat"), ("design", "design")
                ]
                
                for keyword1, keyword2 in duplicate_keywords:
                    if (keyword1 in item_title and keyword2 in completed_lower):
                        is_duplicate = True
                        break
                        
                if is_duplicate:
                    break
            
            if not is_duplicate:
                filtered_items.append(item)
        
        # Ensure we have at least 2 items by adding progression options if needed
        if len(filtered_items) < 2:
            filtered_items.extend(self._get_progression_actions(completed_actions))
            
        return filtered_items[:5]  # Limit to 5 items max
    
    def _get_progression_actions(self, completed_actions: List[str]) -> List[Dict[str, Any]]:
        """Generate progression actions when filtered menu is too small"""
        progression_actions = [
            {
                "title": "Next Phase",
                "prompt": "Move to the next phase of this workflow based on completed work",
                "tools": ["planning"],
                "alt": "Advance to the next stage",
                "icon": "➡️"
            },
            {
                "title": "Deep Dive",
                "prompt": "Explore the most promising aspect from previous work in greater detail",
                "tools": ["analysis"],
                "alt": "Go deeper on key findings",
                "icon": "🔍"
            },
            {
                "title": "Create Deliverable",
                "prompt": "Generate a concrete output based on the work completed so far",
                "tools": ["creation"],
                "alt": "Produce tangible results",
                "icon": "📄"
            }
        ]
        
        # Filter out progression actions that might match completed work
        filtered_progression = []
        for action in progression_actions:
            if not any(action["title"].lower() in completed.lower() for completed in completed_actions):
                filtered_progression.append(action)
                
        return filtered_progression
    
    async def execute_action(
        self, 
        action_id: str, 
        context: Dict[str, Any],
        user_input: str = ""
    ) -> Dict[str, Any]:
        """Execute a selected menu action"""
        
        action_prompt = context.get("action_prompt", "")
        role = context.get("role", "General User")
        previous_context = context.get("context", "")
        parent_content = context.get("parent_content", "")
        
        # Build execution prompt with parent context
        system_prompt = f"""You are an AI assistant specializing in {role} tasks in the UK market.

Use British English, GBP currency, UK demographics and business practices. Avoid US-centric references.

Execute the requested action thoroughly and professionally, building on previous work.

Previous Context: {parent_content[:500] if parent_content else 'No previous context'}

Provide:
1. Detailed results of the action
2. Key insights or findings
3. Specific next steps
4. Any relevant data or recommendations

Be practical, actionable, and build logically on any previous work mentioned."""

        user_prompt = f"""Action to execute: {action_prompt}

Overall Context: {previous_context}

User input: {user_input}

Please execute this action and provide comprehensive results that build on any previous work."""

        try:
            result = await self.ollama.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.ollama.current_model,
                temperature=0.7
            )
            
            # Generate suggested next actions
            next_actions = await self._generate_next_actions(role, result)
            
            return {
                "content": result,
                "next_actions": next_actions,
                "executed_at": "now",
                "model_used": self.ollama.current_model
            }
            
        except Exception as e:
            return {
                "content": f"Error executing action: {str(e)}",
                "next_actions": [],
                "executed_at": "now",
                "model_used": "error"
            }
    
    async def _generate_next_actions(self, role: str, previous_result: str) -> List[str]:
        """Generate suggested next actions based on the result"""
        
        system_prompt = """Generate 3 logical next action titles based on the previous result. 
        Return only a JSON array of strings. Each string should be 2-4 words describing an action.
        
        Example: ["Review Results", "Share Findings", "Plan Implementation"]"""
        
        user_prompt = f"""Role: {role}
Previous result: {previous_result[:500]}...

What are 3 logical next actions that build on these results?"""
        
        try:
            response = await self.ollama.generate_json_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.ollama.current_model
            )
            
            if isinstance(response, list):
                return response[:3]  # Limit to 3 actions
            else:
                return ["Review Results", "Continue Planning", "Next Phase"]
                
        except:
            return ["Review Results", "Continue Planning", "Next Phase"]
    
    def _validate_menu_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean menu items"""
        validated_items = []
        
        for item in items:
            if isinstance(item, dict) and "title" in item:
                validated_item = {
                    "title": item.get("title", "Unknown Action"),
                    "prompt": item.get("prompt", "Execute this action"),
                    "tools": item.get("tools", []),
                    "alt": item.get("alt", item.get("title", "Action")),
                    "icon": item.get("icon", "📋")
                }
                validated_items.append(validated_item)
        
        return validated_items
    
    def _generate_fallback_menu(self, role: str, context: str, completed_actions: List[str] = None) -> List[Dict[str, Any]]:
        """Generate a basic fallback menu when AI generation fails"""
        
        if completed_actions is None:
            completed_actions = []
            
        base_actions = [
            {
                "title": "Analyze Current State",
                "prompt": f"Analyze the current situation for a {role}: {context}",
                "tools": ["analysis"],
                "alt": "Evaluate the present situation",
                "icon": "🔍"
            },
            {
                "title": "Strategic Planning",
                "prompt": f"Create a strategic plan for a {role} dealing with: {context}",
                "tools": ["planning"],
                "alt": "Develop strategic approach",
                "icon": "📋"
            },
            {
                "title": "Research Options",
                "prompt": f"Research available options for a {role} in this context: {context}",
                "tools": ["research"],
                "alt": "Investigate possibilities",
                "icon": "📚"
            },
            {
                "title": "Create Deliverable",
                "prompt": f"Generate a concrete deliverable for a {role} on: {context}",
                "tools": ["creation"],
                "alt": "Produce tangible output",
                "icon": "📄"
            },
            {
                "title": "Next Steps",
                "prompt": f"Determine next steps for a {role} regarding: {context}",
                "tools": ["planning"],
                "alt": "Identify immediate actions",
                "icon": "➡️"
            }
        ]
        
        # Filter fallback actions against completed actions
        return self._filter_completed_actions(base_actions, completed_actions)