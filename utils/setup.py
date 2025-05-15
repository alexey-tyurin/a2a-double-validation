from common.server import A2AServer, InMemoryTaskManager
from config.config import ServerConfig

def setup_a2a_server() -> A2AServer:
    """
    Creates and configures an A2A server instance for local agent communication
    
    Returns:
        A2AServer: Configured A2A server instance
    """
    config = ServerConfig()
    task_manager = InMemoryTaskManager()
    
    server = A2AServer(
        host=config.host,
        port=config.port,
        task_manager=task_manager
    )
    
    return server 