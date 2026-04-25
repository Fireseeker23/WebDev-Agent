import os
from config import CHAR_LIMIT
from google.genai import types

def get_file_content(working_directory, file_path):

    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs


    if not os.path.isfile(target_dir):
        return f'Error: "{file_path}" is not a valid file'

    if valid_target_dir:
        with open(target_dir, 'r') as f:
            content = f.read(CHAR_LIMIT)
            if f.read(1):
                content += f"\n[Content truncated to {CHAR_LIMIT} characters due to length]"
        return content

    else:
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory' 


schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Retrieves the content of a specified file relative to the working directory, with a character limit to prevent excessively long outputs",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Path to the file whose content is to be retrieved, relative to the working directory",
            ),
        },
    ),
)