import requests
import os

class QueryAgent:
    def __init__(self):
        pass            

    def use_llm(self, question):
        """
        Uses a free LLM API to answer the question.
        """
        try:
            api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
            
            # Construct a refined prompt to encourage concise responses
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful and smart assistant. You accurately provide answer to the provided user query.<|eot_id|><|start_header_id|>user<|end_header_id|> Here is the query: "{question}". Provide a precise and concise answer.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
            
            parameters = {
                "max_new_tokens": 3000,  # Limit tokens for conciseness
                "temperature": 0.01,    # Minimize randomness for accuracy
                "top_k": 50,            # Top-k sampling for coherence
                "top_p": 0.95,          # Top-p sampling for relevance
                "return_full_text": False
            }

            response = requests.post(api_url, headers=headers, json={"inputs": prompt, "parameters": parameters})
        
            if response.status_code == 200:
                answer = response.json()[0]['generated_text'].strip()
                return answer
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
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
        Attempts to answer using LLM; falls back to real-time search if necessary.
        """
        answer = self.use_llm(question)
        if not answer or self.requires_real_time_info(answer):
            print("Fallback to real-time API for better accuracy.")
            answer = self.get_real_time_answer(question)
        return answer
    
    def requires_real_time_info(self, answer):
        """
        Checks if the LLM response indicates a lack of real-time information.
        """
        real_time_indicators = [
            "As of my last update",
            "I'm not able to provide real-time",
            "I'd love to help! However, I'm a large language model, I don't have real-time access",
            "I am an AI and do not have real-time access",
            "check the current date", 
            "I can't provide real-time data",
            "I'm not currently able to share the time."
        ]
        generic_responses = ["I'm not sure", "I don't know", "Could you rephrase?"]
        
        # Check for generic or real-time-limited phrases
        return any(indicator in answer for indicator in real_time_indicators + generic_responses)

    