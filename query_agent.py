import requests
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.service_account import IDTokenCredentials
import ollama


class QueryAgent:
    def __init__(self, service_account_path="C:/Users/Amoro/Desktop/Generalquestions/key.json", ollama_host="https://adamodels.datainviz.ai/"):
        # Initialize Ollama client and credentials
        self.ollama_host = ollama_host
        self.token = self._initialize_credentials(service_account_path)
        self.ollama_client = ollama.Client(self.ollama_host, headers={"Authorization": self.token})

    def _initialize_credentials(self, service_account_path):
        """
        Initializes Google service account credentials for the Ollama client.
        """
        credentials = IDTokenCredentials.from_service_account_file(
            service_account_path, target_audience=self.ollama_host
        )
        credentials.refresh(Request())
        return f"Bearer {credentials.token}"

    def use_llm(self, question):
        """
        Uses the Ollama API to answer a question with a structured prompt.
        """
        target_model = "llama3.2:3b"
        structured_prompt = f"""
        You are an intelligent assistant. Respond to the question below in clear and concise language. If you cannot answer, respond in the following structured JSON format:

        {{
            "question": "{question}",
            "answer": "I don't have enough information to answer this.",
            "reason": "I lack real-time data or the knowledge required to answer accurately."
        }}

        Question: {question}
        """
        try:
            response = self.ollama_client.generate(model=target_model, prompt=structured_prompt)
            structured_output = json.loads(response['response'])
             # Check if the LLM indicates a fallback is required
            # if "I don't have enough information" in structured_output["answer"]:
            #     return None
            return structured_output["answer"]  # Extract the "answer" field
        except Exception as e:
            print(f"LLM Error: {e}")
            return None
    def get_real_time_answer(self, question):
        """
        Uses a web search API for real-time answers.
        """
        search_url = f"https://api.bing.microsoft.com/v7.0/search?q={question}"
        headers = {"Ocp-Apim-Subscription-Key": os.getenv("BING_API_KEY")}
        try:
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                results = data.get('webPages', {}).get('value', [])
            
                # Extract snippets and rank by keyword relevance
                if results:
                    snippets = [result['snippet'] for result in results]
                    # Define keywords to increase relevance for typical factual questions
                    keywords = ["currently", "title", "role", "current", "today", "now", "is", "latest", "update", "position"]
                
                    # Filter snippets that mention specific keywords related to "who," "what," "is," "current," etc.
                    relevant_snippets = [
                        snippet for snippet in snippets
                        if any(keyword in snippet.lower() for keyword in keywords) 
                    ]
                
                    # Choose top 2-3 relevant snippets for a more comprehensive response
                    if relevant_snippets:
                        detailed_response = " ".join(relevant_snippets[:2])  # Limit to first 3 snippets for detail
                    else:
                         detailed_response = " ".join(snippets[:1])  # Fallback to first 2 snippets if none match

                    return detailed_response.strip()
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return "Sorry, I couldn't retrieve information at the moment."
        
        except Exception as e:
            print(f"Real-time API Error: {e}")
            return "Error retrieving real-time information."
    
    def answer_question(self, question):
        """
        Answers a question using LLM, with a fallback to real-time search if necessary.
        """
        answer = self.use_llm(question)
        if not answer or self._requires_real_time_info(answer):
            print("Fallback to real-time API for better accuracy.")
            answer = self.get_real_time_answer(question)
        return answer

    def _requires_real_time_info(self, answer):
        """
        Determines if the LLM response indicates a need for real-time information.
        """
        # Fallback response structure used by LLM
        real_time_indicator = "I don't have enough information to answer this."
    
        real_time_indicators = [
             real_time_indicator,
            "As of my last update",
            "I'm not able to provide real-time",
            "I'd love to help! However, I'm a large language model, I don't have real-time access",
            "I am an AI and do not have real-time access",
            "check the current date",
            "I can't provide real-time data",
            "I'm not currently able to share the time.",
            "As of my knowledge cutoff",
            "Unfortunately, I'm a large language model",
            "Not available",
            "Not possible for me to know the current date and time",
            "I'm not capable of displaying real-time information",
            "The current date is not available as I'm a text-based AI model",
            "Today's date is not fixed as I don't have real-time access to current date and time",
            "The current exchange rate is subject to change and may vary depending on the source.",
            "I'm not capable of providing real-time weather information",
            "I'm not aware of the current time as I'm a text-based AI and don't have real-time access to time.",
             "The current time cannot be determined as I am a text-based AI model and do not have access to real-time information"
        ]
        generic_responses = ["I'm not sure", "I don't know", "Could you rephrase?"]
        return any(indicator in answer for indicator in real_time_indicators + generic_responses)