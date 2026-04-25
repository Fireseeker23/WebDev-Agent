import os
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv
from google import genai
from google.genai import types
from agent.functions.get_files_info import schema_get_files_info
from agent.functions.get_file_content import schema_get_file_content
from agent.functions.run_python_file import schema_run_python_file
from agent.functions.write_file import schema_write_file
from agent.functions.master_call_function import call_function

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

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
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)


async def run_agent(
    prompt: str,
    history: list[types.Content] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Async generator that runs the agent loop and yields structured events.

    Args:
        prompt:  The new user message.
        history: Existing conversation history (mutated in-place so the
                 caller can persist it across turns).

    Event shapes:
      { "type": "tool_call",   "data": { "name": str, "args": dict } }
      { "type": "tool_result", "data": str }
      { "type": "text",        "data": str }
      { "type": "error",       "data": str }
    """

    messages: list[types.Content] = history if history is not None else []
    messages.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

    try:
        for _ in range(10):  
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[available_functions],
                ),
            )

            for candidate in response.candidates:
                messages.append(
                    types.Content(role="model", parts=candidate.content.parts)
                )


            if not response.candidates[0].content.parts:
                break

            made_tool_call = False

            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    made_tool_call = True
                    fc = part.function_call

                    yield {
                        "type": "tool_call",
                        "data": {
                            "name": fc.name,
                            "args": dict(fc.args),
                        },
                    }

                    result = await asyncio.to_thread(call_function, fc)

                    if (
                        result.parts is None
                        or result.parts[0].function_response is None
                        or result.parts[0].function_response.response is None
                    ):
                        yield {"type": "error", "data": "Tool call returned an invalid response"}
                        return

                    tool_output = str(result.parts[0].function_response.response)

                    yield {"type": "tool_result", "data": tool_output}

                    messages.append(
                        types.Content(role="user", parts=[result.parts[0]])
                    )
                    await asyncio.sleep(0)

            if not made_tool_call and response.text not in ("", None):
                yield {"type": "text", "data": response.text}
                break

    except Exception as e:
        yield {"type": "error", "data": str(e)}
