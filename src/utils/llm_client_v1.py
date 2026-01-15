"""
Simplified LLM client for testing.
"""
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

# Mock mode for testing without API calls
MOCK_MODE = True  # Set to False when you have a real API key

def call_llm(
    prompt: str, 
    model_name: str = "gemini-1.5-flash",
    temperature: float = 0.1,
    max_tokens: int = 1000
) -> str:
    """
    Call Gemini API or return mock response.
    """
    if MOCK_MODE:
        print(f"🔧 MOCK MODE: Simulating LLM call to {model_name}")
        time.sleep(0.5)  # Simulate API delay
        
        # Return mock responses based on prompt content
        if "FIXER" in prompt or "fix" in prompt.lower():
            # Mock fixer response
            if "z = x + y" in prompt:
                return '''def calculate_sum(a, b):
    # This function adds two numbers
    result = a + b
    return result  # Fixed typo

x = 5
y = "10"
z = x + int(y)  # Fixed type error'''
            else:
                return '''def old_function(x):
    """Returns double the input."""
    return x * 2'''
        
        elif "AUDITOR" in prompt or "analyze" in prompt.lower():
            # Mock auditor response
            return json.dumps({
                "issues_found": 2,
                "refactoring_plan": [
                    {
                        "priority": "CRITICAL",
                        "issue": "Type error adding int and str",
                        "line": 7,
                        "code_snippet": "z = x + y",
                        "suggestion": "Convert y to int: z = x + int(y)"
                    },
                    {
                        "priority": "HIGH",
                        "issue": "Variable name typo",
                        "line": 4,
                        "code_snippet": "return results",
                        "suggestion": "Fix variable name: return result"
                    }
                ],
                "pylint_score": 6.5,
                "summary": "Two critical issues found"
            })
        
        else:
            return "Mock response from LLM"
    
    else:
        # Real API call
        try:
            from google import genai
            from google.genai import types
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return "ERROR: No API key found in .env file"
            
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            return response.text if response.text else "No response generated"
            
        except ImportError:
            print("❌ google-generativeai not installed properly")
            print("Try: pip install --upgrade google-generativeai")
            return "ERROR: google-generativeai not installed"
        except Exception as e:
            return f"ERROR: {str(e)}"