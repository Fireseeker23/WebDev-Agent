#CLI Version of the agent

import os
from dotenv import load_dotenv
from google import genai
import argparse
from google.genai import types
from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.run_python_file import run_python_file, schema_run_python_file
from functions.write_file import write_file, schema_write_file
from functions.master_call_function import call_function

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)


system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories (get_files_info)
- Read file contents (Used to getting the content of files) (get_file_content)
- Run Python files (If the user asks to run a Python file.) (run_python_file)
- Write or overwrite files (write_file)

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.

You will be provided with the results of your function calls, which you can use to make further function calls or to answer the user's question. Always use the results from your function calls to inform your next steps.
"""

available_functions = types.Tool(
    function_declarations=[schema_get_files_info,schema_get_file_content, schema_run_python_file, schema_write_file],

)


parser = argparse.ArgumentParser(description='User Input')
parser.add_argument('input', type=str, help='Input for the model')
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

messages = [
    types.Content(
        role="user",
        parts=[types.Part(text=args.input)]
    )
]


for _ in range(5):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
        config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[available_functions])
    )

    for candidate in response.candidates:
        messages.append(types.Content(role="model", parts=candidate.content.parts))

    if response.usage_metadata is not None and args.verbose:
        print("User prompt:", args.input)
        print("Prompt tokens:", response.usage_metadata.prompt_token_count)
        print("Response tokens:", response.usage_metadata.candidates_token_count)

    if not response.candidates[0].content.parts:
        break

    for part in response.candidates[0].content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            function_call_result = call_function(part.function_call, verbose=args.verbose)
            
            if(function_call_result.parts==None):
                raise Exception("Something went wrong")
            if(function_call_result.parts[0].function_response==None):
                raise Exception("Something went wrong")
            if(function_call_result.parts[0].function_response.response == None):
                raise Exception("Something went wrong")
            
            function_results = [function_call_result.parts[0]]
            if args.verbose:
                print(f"-> {function_call_result.parts[0].function_response.response}")
            
            messages.append(types.Content(role="user", parts=function_results))

    if(response.text not in ["", None]):
        print(response.text)
