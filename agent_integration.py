from dotenv import load_dotenv
from flask import Flask
import sys
import signal
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
from router.helper.utils import RegistrationHelper, MessageHelper
from router.models.chain_of_thought import AgentDescriptor, COTRequest, COTResponse
from router.models.configs import RabbitMQConfig
from query_agent import QueryAgent  # Import QueryAgent

rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")
rabbitmq_user = os.getenv("RABBITMQ_USER")
rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
rabbitmq_virtual_host = os.getenv("RABBITMQ_VHOST")

rabbit_config = RabbitMQConfig(
    host=rabbitmq_host,
    port=rabbitmq_port,
    user=rabbitmq_user,
    password=rabbitmq_password,
    virtual_host=rabbitmq_virtual_host
)

# Agent descriptor
agentDescription = AgentDescriptor.model_validate({
    "identifier": "general_questions",
    "purpose": [
        "Answer general questions using LLM",
        "Fallback to real-time API if necessary"
    ],
    "agent_type": "other"
})

# Registration helper
registrationHelper = RegistrationHelper(
    host="http://localhost:5000",
    agent_descriptor=agentDescription
)
registrationHelper.register()

# Message helper
messageHelper = MessageHelper(
    config=rabbit_config,
    agent_descriptor=agentDescription
)

# Initialize QueryAgent
query_agent = QueryAgent()

# Define message processing
def on_message(message: COTRequest):
    print("Received message: ", message)

    # Extract question from message
    question = message.action

    # Get answer using QueryAgent
    answer = query_agent.answer_question(question)

    # Build response
    response = COTResponse.model_validate({
        "action": "general_questions",
        "user_identifier": message.user_identifier,
        "prompt_identifier": message.prompt_identifier,
        "action_successful": bool(answer),
        "action_response": answer if answer else "Could not process the question."
    })

    # Send response
    messageHelper.send_message(response)

# Register message consumer
messageHelper.add_consumer(on_message_received=on_message)

# Graceful shutdown
def onClose(exception=None):
    messageHelper.remove_consumer()
    registrationHelper.unregister()
    print("App Closed!!")

def handle_sigterm(*args): 
    onClose() 
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_sigterm)
    app.run(debug=True, port=5003)

