import re
from openai import OpenAI

# Initialize Ollama Client
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# Tool A: Keyword Extractor
def extract_keywords(text):
    return [word.strip(".,!?") for word in text.split() if len(word) > 4]

def spell_check_and_correct(text):
    """
    Uses a smaller LLM to detect and correct spelling errors.
    Returns corrected text and a flag indicating if corrections were made.
    """
    try:
        completion = client.chat.completions.create(
            model="llama3.2:1b",  # Using a smaller, faster model for spell checking
            messages=[
                {
                    "role": "system", 
                    "content": """You are an expert spell checker. Your ONLY job is to correct spelling mistakes.

CRITICAL RULES:
1. ONLY fix obvious spelling errors - do NOT change correctly spelled words
2. Preserve the original meaning, grammar, and sentence structure exactly
3. Do NOT rephrase, rewrite, or change the wording
4. Do NOT change numbers, math expressions, or mathematical operators (+, -, *, /, =)
5. Do NOT add or remove words
6. Do NOT change capitalization unless it's clearly wrong
7. If a word could be spelled multiple ways, choose the most common spelling
8. If you're unsure about a word, leave it unchanged
9. Return ONLY the corrected text with no explanations or comments
10. Do NOT add phrases like "Corrected text:", "Output:", or any prefixes

Examples:
- Input: "I want to lern about artifical inteligence" 
  Output: "I want to learn about artificial intelligence"
- Input: "25+25"
  Output: "25+25"
- Input: "What is machine learning?"
  Output: "What is machine learning?"
- Input: "Searh for informaton about quantim computing"
  Output: "Search for information about quantum computing"
"""
                },
                {
                    "role": "user", 
                    "content": f"Correct only the spelling errors in this text:\n\n{text}"
                }
            ],
            temperature=0.0,  # Very low temperature for consistent corrections
            max_tokens=len(text.split()) * 3  # More generous token limit
        )
        corrected_text = completion.choices[0].message.content.strip()
        
        # Clean up any extra formatting the model might add
        corrected_text = corrected_text.replace('"', '').replace("'", "'")
        
        # Check if corrections were made (case-insensitive comparison)
        corrections_made = corrected_text.lower().strip() != text.lower().strip()
        
        return corrected_text, corrections_made
        
    except Exception as e:
        print(f"Spell check error: {e}")
        return text, False  # Return original text if spell check fails

# Tool B: Mock Web Search
def mock_web_search(keywords):
    return f"Search results for: {', '.join(keywords)}. Example content about {keywords[0]} and its importance."


# Tool C: Qwen Summarizer
def summarize_with_qwen(text):
    completion = client.chat.completions.create(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": "You are a helpful summarizer."},
            {"role": "user", "content": f"Summarize the following:\n\n{text}"}
        ]
    )
    return completion.choices[0].message.content


# Tool D: Calculator
def evaluate_math_expression(expression):
    try:
        # VERY simple safe eval for math only
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result is: {result}"
    except Exception as e:
        return f"Error evaluating expression: {e}"


# Tool Router: Detect if input is math
def is_math_expression(text):
    return bool(re.fullmatch(r"[\d\s\+\-\*\/\.\(\)]+", text.strip()))


# Main Orchestrator
def multi_tool_assistant(user_input):
    print("Original User Input:", user_input)
    
    # Spell check first (before any other processing)
    print("\n🔍 Running spell check...")
    corrected_input, corrections_made = spell_check_and_correct(user_input)
    
    if corrections_made:
        print(f"✅ Spelling corrections applied:")
        print(f"   Original: {user_input}")
        print(f"   Corrected: {corrected_input}")
    else:
        print("✅ No spelling errors detected.")

    if is_math_expression(user_input):
        print("🧮 Detected math input. Routing to Calculator.")
        result = evaluate_math_expression(user_input)
        print("Tool D - Calculator:\n", result)
        return
    
    # Use corrected input for all other processing
    keywords = extract_keywords(corrected_input)
    print("Tool A - Extracted Keywords:", keywords)

    search_results = mock_web_search(keywords)
    print("Tool B - Search Result:\n", search_results)

    summary = summarize_with_qwen(search_results)
    print("\nTool C - Qwen Summary:\n", summary)


# Run Demo
if __name__ == "__main__":
    examples = [
        # "Tell me about the impact of solar power on rural communities.",
        #  "25*(3+7)",
        # "I want to lern about artifical inteligence",  # Test with spelling errors
        # "Searh for informaton about quantim computing",  # Test with more errors
        "What is the lrgest planet in Soler System?"
    ]
    for query in examples:
        print("\n" + "="*50)
        multi_tool_assistant(query)