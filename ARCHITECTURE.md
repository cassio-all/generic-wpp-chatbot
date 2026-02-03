# Architecture

## System Overview

The Generic WhatsApp Chatbot is built with a modular architecture using LangGraph for agent orchestration and Kestra for workflow automation.

```
┌─────────────────────────────────────────────────────────────────┐
│                        WhatsApp User                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ Message
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Main Orchestrator                             │
│                      (LangGraph)                                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Router Agent (GPT-4o-mini)                  │   │
│  │         Determines user intent from message              │   │
│  └────────┬─────────────────────────────────────────────────┘   │
│           │                                                       │
│           ├──────────────┬──────────────┬──────────────┐        │
│           ▼              ▼              ▼              ▼        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ Knowledge  │  │  Calendar  │  │   Email    │  │ General  │ │
│  │   Agent    │  │   Agent    │  │   Agent    │  │   Chat   │ │
│  └────┬───────┘  └────┬───────┘  └────┬───────┘  └────┬─────┘ │
│       │              │              │              │            │
└───────┼──────────────┼──────────────┼──────────────┼───────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐
│ Knowledge    │ │ Google       │ │ SendGrid     │ │ OpenAI     │
│ Base Tool    │ │ Calendar API │ │ Email API    │ │ GPT-4o     │
│ (ChromaDB)   │ │              │ │              │ │            │
└──────────────┘ └──────────────┘ └──────────────┘ └────────────┘
```

## Agent Architecture

### 1. Router Agent
- **Purpose**: Analyzes incoming messages and determines user intent
- **Model**: GPT-4o-mini (fast and cost-effective)
- **Outputs**: Intent classification (knowledge_query, schedule_meeting, send_email, general_chat)

### 2. Knowledge Agent
- **Purpose**: Answers questions using the knowledge base
- **Model**: GPT-4o-mini
- **Tools**: 
  - `search_knowledge_base()`: Retrieves relevant documents from vector DB
- **Process**:
  1. Searches ChromaDB for relevant documents
  2. Constructs prompt with context
  3. Generates response using LLM

### 3. Calendar Agent
- **Purpose**: Schedules meetings on Google Calendar
- **Model**: GPT-4o-mini
- **Tools**:
  - `schedule_meeting()`: Creates calendar events
  - `list_upcoming_events()`: Lists scheduled events
- **Process**:
  1. Extracts meeting details from message
  2. Validates required information
  3. Creates event via Google Calendar API

### 4. Email Agent
- **Purpose**: Sends emails via SendGrid
- **Model**: GPT-4o-mini
- **Tools**:
  - `send_email()`: Sends emails
- **Process**:
  1. Extracts email details from message
  2. Validates required information
  3. Sends email via SendGrid API

### 5. General Chat Agent
- **Purpose**: Handles general conversation
- **Model**: GPT-4o-mini (higher temperature for natural conversation)
- **Process**:
  1. Maintains conversation history
  2. Generates contextual responses

## State Management

The system uses LangGraph's state management with the following structure:

```python
AgentState = {
    "messages": List[BaseMessage],     # Conversation history
    "intent": str,                      # Classified user intent
    "sender": str,                      # User identifier
    "should_use_tools": bool,          # Whether to use external tools
    "response": str                     # Final response to user
}
```

## Data Flow

1. **Message Reception**: User sends message to WhatsApp
2. **State Initialization**: Create initial AgentState with message
3. **Intent Classification**: Router Agent determines intent
4. **Agent Routing**: Graph routes to appropriate specialized agent
5. **Tool Execution**: Agent calls relevant tools if needed
6. **Response Generation**: Agent generates response using LLM
7. **Message Sending**: Response sent back to user

## Kestra Orchestration

Kestra provides workflow automation for:

### Main Chatbot Workflow (`whatsapp-chatbot-main.yml`)
- Processes incoming WhatsApp messages
- Triggers agent graph execution
- Handles response delivery

### Knowledge Base Update (`knowledge-base-update.yml`)
- Scheduled daily at 2 AM
- Rebuilds vector database from knowledge_base/ directory
- Ensures knowledge base stays current

### Scheduled Reports (`scheduled-reports.yml`)
- Sends daily reports at 9 AM
- Email delivery via SendGrid
- Customizable report types

## Knowledge Base System

### Vector Database (ChromaDB)
- **Embeddings**: OpenAI text-embedding-ada-002
- **Storage**: Persistent local storage in `data/vector_db/`
- **Chunking**: 1000 characters with 200 character overlap

### Document Processing
1. Load documents from `knowledge_base/` directory
2. Split into chunks using RecursiveCharacterTextSplitter
3. Generate embeddings using OpenAI
4. Store in ChromaDB with metadata

### Retrieval
1. User query embedded using same model
2. Similarity search in vector database
3. Top-k relevant documents returned
4. Documents used as context for LLM response

## Deployment Architecture

### Docker Compose Services

1. **chatbot**: Main application
   - Python 3.11
   - Exposes port 8000
   - Mounts volumes for data persistence

2. **kestra**: Workflow orchestration
   - Kestra latest version
   - Exposes port 8080 (Web UI)
   - PostgreSQL backend

3. **postgres**: Database for Kestra
   - PostgreSQL 15
   - Persistent storage

## Security Considerations

- API keys stored in environment variables
- Credentials isolated in `credentials/` directory
- Vector database and logs excluded from version control
- OAuth tokens for Google Calendar securely stored

## Scalability

The architecture supports scaling through:

1. **Horizontal Scaling**: Multiple chatbot instances behind load balancer
2. **Agent Parallelization**: LangGraph supports parallel agent execution
3. **Vector DB Sharding**: ChromaDB can be replaced with distributed alternatives
4. **Kestra Distribution**: Kestra supports distributed execution

## Extensibility

### Adding New Agents
1. Create agent class in `src/agents/`
2. Define processing logic
3. Register in `orchestrator.py`
4. Update router logic

### Adding New Tools
1. Create tool function in `src/tools/`
2. Implement API integration
3. Import in agent that needs it
4. Update tool documentation

### Adding New Knowledge
1. Add `.txt` files to `knowledge_base/`
2. Rebuild vector DB (automatic on startup or via Kestra workflow)

## Monitoring and Observability

- **Structured Logging**: JSON formatted logs with structlog
- **Kestra UI**: Visual workflow monitoring at localhost:8080
- **Log Storage**: Persistent logs in `logs/` directory
- **Metrics**: Available through Kestra execution history

## Performance Characteristics

- **Router Agent**: ~500ms response time
- **Knowledge Retrieval**: ~200-300ms search time
- **LLM Generation**: ~1-3s depending on response length
- **Total Request**: ~2-5s end-to-end
