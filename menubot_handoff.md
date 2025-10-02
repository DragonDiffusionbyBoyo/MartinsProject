# MenuBot Project Handoff Document
**Date**: September 5, 2025  
**Current Status**: Phase 1 Complete - Backend Functional  
**Next Phase**: Frontend Development

## Project Overview

MenuBot is a dynamic AI workflow builder that creates context-aware menu systems for any professional role. Each menu choice spawns AI agents to execute actual work, with visual node graphs showing workflow progression.

### Core Concept
- Right-click context menus generate AI-powered action options
- Each action creates new nodes in a visual workflow tree
- 1M token context maintains entire workflow state
- Context-aware menu generation based on previous actions

## Current Implementation Status

### ✅ Phase 1 Complete: Backend Infrastructure

**Working Components:**
- FastAPI server running on port 8000
- SQLite database with nodes, actions, and context tables
- Ollama integration with 1M context model
- Menu generation and action execution endpoints
- Configuration system (settings.py)

**API Endpoints:**
- `GET /api/health` - System health check
- `GET /api/models` - List available Ollama models
- `POST /api/generate-menu` - Generate context-aware menu options
- `POST /api/execute-action` - Execute selected action with AI
- `POST /api/set-model` - Change active model

### Test Results
**Successful test case:**
- Role: "Marketing Director"
- Context: "Planning campaign for new shoes"
- User input: "Focus on target demographics"
- Output: Comprehensive 2000+ word marketing analysis with actionable insights

## Model Configuration

### Primary Model (Active)
**`danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth`**
- Size: 17GB (Q4_K_XL quantization)
- Context: 1,000,000 tokens
- Performance: Excellent reasoning and detailed output
- VRAM: ~18GB
- Status: Downloaded and tested successfully

### Available Models
1. **VLM Option**: `redule26/huihui_ai_qwen2.5-vl-7b-abliterated:latest`
   - Size: 6GB
   - Context: 125,000 tokens
   - Features: Vision + uncensored
   - Status: Available for vision tasks

2. **Speed Option**: `polaris:latest`
   - Size: 4.3GB
   - AIME Score: 79.4 (high performance)
   - Status: Available for quick responses

3. **Fallback**: `qwen3:30b`
   - Size: 18GB
   - Status: Reliable general model

### Model Testing Strategy
**Phase 2 Requirements:**
- Test VLM capabilities for document/image analysis
- Compare Unsloth vs VLM for different workflow types
- Determine optimal model switching logic
- Implement model selection based on task type

## Technical Architecture

### File Structure
```
F:\Githubrepostotest\MartinsProject\
├── backend/
│   ├── main.py              # FastAPI server
│   ├── ollama_client.py     # Ollama integration
│   ├── menu_generator.py    # AI menu logic
│   ├── settings.py          # Configuration system
│   └── database/            # SQLite database
├── config/                  # Config files
├── requirements.txt         # Python dependencies
└── requirements_media.txt   # Media processing deps
```

### Database Schema
- **nodes**: Workflow decision points with parent relationships
- **actions**: Menu choices with prompts and tools
- **context**: Session state and conversation history

### Hardware Requirements
- **Development**: 2x A5000s (48GB total)
- **Deployment**: 24GB VRAM target for Martin
- **OS Support**: Windows (current), Linux (target)

## Phase 2: Frontend Development

### Required Components

**1. Visual Node Graph**
- React component with node visualization
- Drag/drop workflow building
- Node connections showing workflow flow
- Different node types (menu, result, input)

**2. Context Menu System**
- Right-click menu generation
- Dynamic options based on AI responses
- Integration with backend menu generation API
- Visual menu styling and UX

**3. AI Integration Interface**
- Display AI-generated menu options from backend
- Action execution with loading states
- Result display in new nodes
- Progress tracking for multi-step workflows

**4. Canvas Management**
- Zoom/pan functionality
- Save/load workflow states
- Export workflow as documents
- Undo/redo functionality

### Technical Stack Recommendations
**Frontend Framework**: React with TypeScript
**Node Graph Library**: React Flow or D3.js
**Styling**: Tailwind CSS
**State Management**: React Context or Zustand
**API Client**: Axios for backend communication

### Context Awareness Implementation
The 1M context model enables:
- **Full workflow memory**: Entire conversation history in model context
- **Smart menu generation**: Each menu considers all previous actions
- **Contextual suggestions**: Next actions based on complete workflow state
- **Dynamic adaptation**: Menu options evolve as workflow progresses

## Development Environment

### Running the Backend
```bash
cd F:\Githubrepostotest\MartinsProject\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Generate menu
curl -X POST "http://localhost:8000/api/generate-menu" \
  -H "Content-Type: application/json" \
  -d '{"role": "Marketing Director", "context": "Planning campaign"}'

# Execute action
curl -X POST "http://localhost:8000/api/execute-action" \
  -H "Content-Type: application/json" \
  -d '{"action_id": "test", "context": {...}, "user_input": "..."}'
```

### Model Management
```bash
# Load model
ollama run danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth

# Check loaded models
ollama ps

# List available models
ollama list
```

## Known Issues and Considerations

### Current Limitations
1. **CLI Interface Only**: No visual frontend yet
2. **Model Switching**: Manual process, needs automation
3. **Error Handling**: Basic implementation, needs enhancement
4. **Security**: No authentication or rate limiting

### Phase 2 Priorities
1. **Frontend Development**: Visual workflow builder
2. **Model Intelligence**: Automatic model selection based on task
3. **VLM Integration**: Image/document processing capabilities
4. **User Experience**: Polish and usability improvements

## Deployment Strategy

### For Martin (Linux)
- Docker container with all dependencies
- Single command deployment
- Environment variable configuration
- 24GB VRAM optimization

### Model Configuration Options
- **Lightweight**: VLM (6GB) + Speed model (4GB) = 10GB total
- **Balanced**: Unsloth (18GB) + VLM (6GB) = 24GB total
- **Performance**: Unsloth only (18GB) with model swapping

## Next Steps

### Immediate Phase 2 Tasks
1. **Frontend Setup**: Create React application structure
2. **Node Graph**: Implement visual workflow canvas
3. **API Integration**: Connect frontend to working backend
4. **Context Menus**: Implement right-click menu system
5. **Testing**: Validate full workflow with visual interface

### Long-term Enhancements
- Plugin system for custom tools
- Workflow templates and sharing
- Advanced model management
- Performance optimization
- Multi-user support

## Success Metrics

### Phase 1 Achieved
- ✅ Backend API functional
- ✅ AI integration working
- ✅ 1M context model deployed
- ✅ Database persistence
- ✅ Quality AI output demonstrated

### Phase 2 Targets
- Visual workflow building in under 30 seconds
- Context-aware menu generation 90%+ relevance
- Smooth model switching between tasks
- Complete 5-step workflow without confusion
- Responsive, intuitive user interface

## Contact and Resources

**Project Repository**: `F:\Githubrepostotest\MartinsProject\`  
**Primary Model**: 1M context Qwen3-Coder (17GB)  
**API Documentation**: http://localhost:8000/docs  
**Database**: SQLite at `backend/database/menubot.db`

The backend foundation is solid and tested. The 1M context capability provides the memory needed for complex workflows. Phase 2 focus should be creating an intuitive visual interface that leverages this powerful backend infrastructure.