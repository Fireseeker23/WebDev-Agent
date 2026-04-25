import os
from google.genai import types


def write_file(working_directory, file_path, content):

    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs

    if os.path.isdir(target_dir):
        return f'Error: "Cannot write to {file_path}" as it is a directory'

    os.makedirs(os.path.dirname(target_dir), exist_ok=True)

    if valid_target_dir:
        with open(target_dir, 'w') as f:
            f.write(content)
        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'

    else:
        return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'



    
schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes content to a specified file relative to the working directory, creating any necessary directories. Prevents writing to locations outside the working directory for security.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Path to the file whose content is to be written, relative to the working directory",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to the file",
            ),
        },
    ),
)