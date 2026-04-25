import os
import subprocess
from google.genai import types


def run_python_file(working_directory, file_path, args=None):

    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))
    valid_target_dir = os.path.commonpath([working_dir_abs, target_dir]) == working_dir_abs

    if os.path.isdir(target_dir):
        return f'Error: "Cannot run {file_path}" as it is a directory'
    if not os.path.isfile(target_dir):
        return f'Error: "{file_path}" does not exist'
    if not target_dir.endswith('.py'):
        return f'Error: "{file_path}" is not a Python file'
    if not valid_target_dir:
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

    

    command = ["python", target_dir]
    command.extend(args or [])
    CompletedProcess = subprocess.run(command, check=True, cwd=working_dir_abs, capture_output=True, text=True, timeout=30)

    if CompletedProcess.returncode != 0:
        return f"Process exited with code {CompletedProcess.returncode}"
    if not CompletedProcess.stdout and not CompletedProcess.stderr:
        return f"Process did not produce any output"
    
    output = f"STDOUT: {CompletedProcess.stdout.strip()}\nSTDERR: {CompletedProcess.stderr.strip()}"    

    return output


schema_run_python_file = types.FunctionDeclaration(
name="run_python_file",
description="Runs a specified Python file relative to the working directory",
parameters=types.Schema(
    type=types.Type.OBJECT,
    properties={
        "file_path": types.Schema(
            type=types.Type.STRING,
            description="Path to the file whose content is to be retrieved, relative to the working directory",
        ),
        # "args": types.Schema(
        #     type=types.Type.ARRAY,
        #     items=types.Schema(type=types.Type.STRING),
        #     description="Optional list of string arguments to pass to the Python file when executing",
        # ),
    },
),
)