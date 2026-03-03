from modelgauge.prompt import ChatPrompt, TextPrompt 

from modelgauge.prompt_formatting import format_chat 

from modelgauge.sut import PromptResponseSUT, SUTResponse 

from modelgauge.sut_capabilities import AcceptsChatPrompt, AcceptsTextPrompt 

from modelgauge.sut_decorator import modelgauge_sut 

from modelgauge.sut_registry import SUTS 

from pydantic import BaseModel 

import requests 

import json  # <-- Missing import 

 

class DeepSeekSUTRequest(BaseModel): 

    prompt: str 

    model: str = "deepseek-r1:8b" #CHANGE TO YOUR OLLAMA MODEL  

    stream: bool = False 

 

class DeepSeekSUTResponse(BaseModel): 

    response: str 

 

@modelgauge_sut(capabilities=[AcceptsTextPrompt, AcceptsChatPrompt]) 

class DeepSeekSUT(PromptResponseSUT): 

    def translate_text_prompt(self, prompt: TextPrompt, options: dict = None) -> DeepSeekSUTRequest: 

        return DeepSeekSUTRequest(prompt=prompt.text) 

 

    def translate_chat_prompt(self, prompt: ChatPrompt, options: dict = None) -> DeepSeekSUTRequest: 

        return DeepSeekSUTRequest(prompt=format_chat(prompt)) 

 

    def evaluate(self, request: DeepSeekSUTRequest) -> DeepSeekSUTResponse: 

        ollama_url = "http://localhost:11434/api/generate" 

 

        payload = { 

            "prompt": request.prompt, 

            "model": request.model, 

            "stream": request.stream, 

        } 

 

        try: 

            response = requests.post(ollama_url, json=payload, stream=request.stream) 

            response.raise_for_status() 

 

            if request.stream: 

                full_response = "" 

                for line in response.iter_lines(): 

                    if line: 

                        try: 

                            data = json.loads(line.decode("utf-8")) 

                            if "response" in data: 

                                full_response += data["response"] 

                            if data.get("done", False): 

                                break 

                        except json.JSONDecodeError: 

                            print("Error decoding JSON from stream.") 

                return DeepSeekSUTResponse(response=full_response) 

            else: 

                return DeepSeekSUTResponse(response=response.json()["response"]) 

 

        except requests.exceptions.RequestException as e: 

            raise Exception(f"Error communicating with Ollama: {e}") 

 

    def translate_response(self, request: DeepSeekSUTRequest, response: DeepSeekSUTResponse) -> SUTResponse: 

        return SUTResponse(text=response.response) 

 

SUTS.register(DeepSeekSUT, "DeepSeekSUT") 