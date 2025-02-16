from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Question_answering.RoundOne.apis import first_round_app
from Question_answering.RoundTwo.apis import second_round_app
from Question_answering.RoundFour.apis import fourth_round_app
from Question_answering.AIAgent.Agent import AI_agent_app
from quizExperience.websockets import multiplayer
import logging
from logging.config import dictConfig
import uvicorn
import threading
import signal
import sys

# Define logging configuration
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "simple",
            "level": "INFO"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}

# Configure logging
dictConfig(log_config)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routers
app.include_router(first_round_app, prefix="/first_round")
app.include_router(second_round_app, prefix="/second_round")
app.include_router(fourth_round_app, prefix='/fourth_round')
app.include_router(AI_agent_app, prefix="/agent")
app.include_router(multiplayer, prefix="/multiplayer")

# Create a server instance that can be stopped
server = None

@app.get("/shutdown")
async def shutdown():
    """Endpoint to shutdown the server"""
    if server:
        server.should_exit = True
    return {"message": "Server shutting down"}

def run_server():
    global server
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_config=None,
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == '__main__':
    # Run the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # Handle shutdown signals
    def signal_handler(signum, frame):
        if server:
            server.should_exit = True
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)




    """
        Original Script below
        The script included terminal logging which I removed to enhance user experience in the main application
    """


# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# # from Text_to_Speech.TextToSpeech import tts_app
# from Question_answering.RoundOne.apis import first_round_app
# from Question_answering.RoundTwo.apis import second_round_app
# from Question_answering.RoundFour.apis import fourth_round_app
# from Question_answering.AIAgent.Agent import AI_agent_app
# # from new_questions.api import new_questions
# from quizExperience.websockets import multiplayer

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[''],
#     allow_credentials=True,
#     allow_methods=[''],
#     allow_headers=['*'],
# )

# # app.include_router(tts_app, prefix="/tts")
# app.include_router(first_round_app, prefix="/first_round")
# app.include_router(second_round_app, prefix="/second_round")
# app.include_router(fourth_round_app, prefix='/fourth_round')
# # app.include_router(new_questions, prefix='/new-questions')
# app.include_router(AI_agent_app, prefix="/agent")
# app.include_router(multiplayer, prefix="/multiplayer")

# if name == 'main':
#     import uvicorn
#     uvicorn.run(app, host='0.0.0.0', port=8000)