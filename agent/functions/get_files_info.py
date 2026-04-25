import os
from pathlib import Path
from google.genai import types

def get_files_info(working_directory, directory="."):
    output_string = f'Results for {directory}:\n'

    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, directory))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs


    if not os.path.isdir(target_dir):
        output_string += f'Error: "{directory}" is not a valid directory'
        return output_string

    if valid_target_dir:
        for filename in os.listdir(target_dir):
            full_path = os.path.join(target_dir, filename)
            file_size = os.path.getsize(full_path)
            is_dir = os.path.isdir(full_path)
            output_string += f'{filename}: file_size={file_size} bytes, is_dir={is_dir}\n'

    else:
        output_string += f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    return output_string




schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in a specified directory relative to the working directory, providing file size and directory status",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="Directory path to list files from, relative to the working directory (default is the working directory itself)",
            ),
        },
    ),
)

