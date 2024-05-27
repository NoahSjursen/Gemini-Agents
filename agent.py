import os
import dotenv
import json
import google.generativeai as genai
import sys
import subprocess
import random
import string

dotenv.load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    safety_settings=safety_settings,
    generation_config=generation_config,
)

def request_gemini_to_generate(user_input):
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(user_input)
    return response.text.replace("```", "").replace("````python", "").replace("python", "")


def generate_plan(agent_data):
    task = agent_data['task']
    role = agent_data['role']
    codesnippets = agent_data['codesnippets']  # List of file names
    codesnippetstext = ""
    folder = agent_data['folder']
    if folder is not None:
        OpenFolder(folder, role,task)  # Call the OpenFolder() function if 'folder' is not None
        return
    
    prompt = f"""
    You are a "{role}" tasked with "{task}".
    The task should be completed as a single solution, not multiple projects.

    ## Input Data:
    [Describe the input data format]

    ## Output:
    [Describe the desired output format]

    ## Constraints:
    [Specify any limitations]

    ## Evaluation Criteria:
    [List criteria for assessing the plan]

    ## Error Handling:
    [Mention the need to address potential errors]

    ##Code Snippets that the user has used to guide you to make a cohesive plan of action. Explain what snippets need to be added into the file:

    """
    # Loop through the file names and read content
    for filename in codesnippets:
        file_path = os.path.join("codesnippets", filename)  # Join path with "codesnippets" folder
        if os.path.isfile(file_path):  # Check if the file exists
            with open(file_path, 'r') as file:
                code_snippet = file.read()
                codesnippetstext += code_snippet
                prompt += f"```\n{code_snippet}\n```\n"
        else:
            print(f"Warning: File not found: {file_path}")  # Print a warning if file not found

    prompt += "## File Structure:\n[Describe the proposed file structure for the task. This can include the number of files, their names, and their intended functions. The files can be of various types, including code files, text files, data files, etc., and don't need to be related to a specific project. The goal is to outline a logical organization for the content generated.]"
    plan_response = request_gemini_to_generate(prompt)
    get_filenames(plan_response,role,task,codesnippetstext)


def OpenFolder(folder, role, task):
    folder_path = os.path.join("agents", folder)  # Construct the full path to the folder
    print(f"Opening folder '{folder_path}'")

    for filename in os.listdir(folder_path):
        if filename.endswith((".py", ".txt", ".json", ".csv", ".md")):  # Check for common file types
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r") as file:
                original_content = file.read()

            # Prompt for improvements or additions
            prompt = f"""
            You are a {role} tasked with {task}. 
            Improve or add to the following code snippet, considering the overall goals of the task.

            ```
            {original_content}
            ```

            **Instructions:**
            - If the code snippet is incomplete, add the necessary code to fulfill the task.
            - If the code is incorrect, fix any errors.
            - If the code is inefficient, optimize it for performance.
            - If the code is not well-structured, improve its readability and organization.
            - Return Only the new and edited code. No explanations needed
            """

            # Generate improved code
            improved_code = request_gemini_to_generate(prompt)

            # Write the improved code back to the file
            with open(filepath, "w") as file:
                file.write(improved_code)

            print(f"File '{filename}' updated.")


def get_filenames(plan_response,role,task,codesnippetstext):
    # Analyze the plan to extract file names
    file_names = []
    prompt_filenames = f"You are tasked with finding the files required in this project. look for text with 'Create a file named: 'filename' ' for each file you find. add to a list with filenames only seperated by comma. here is the info to look through: {plan_response} use no other formatting such as '' when placing into the string"
    file_names = request_gemini_to_generate(prompt_filenames)
    print(file_names)
    file_names = file_names.split(",")
    # Clean up the filenames
    clean_file_names = []
    for file_name in file_names:
        file_name = file_name.strip()  # Remove leading/trailing spaces and newlines
        file_name = file_name.replace('\n', '') # Remove any remaining newline characters
        clean_file_names.append(file_name)

    print(clean_file_names)
    create_folder(clean_file_names,role,task,plan_response,codesnippetstext)







def create_folder(clean_file_names, role, task, plan_response,codesnippetstext):

    # Generate a random 10-character string
    folder_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

    print(folder_name)

    os.makedirs(folder_name, exist_ok=True)
    create_file(folder_name,clean_file_names,role,task,plan_response,codesnippetstext)




def create_file(folder_name,clean_file_names,role,task,plan_response, codesnippetstext):
    for i, file_name in enumerate(clean_file_names):
        file_path = os.path.join(folder_name, file_name)
        try:
            with open(file_path, 'w') as f:

                #Creates a plan for the specific file:
                file_plan_prompt = f"""{role}\n\n{task}\n\nCreate a detailed plan for: "{file_name}\n\n\nYou should read details from the general plan for this project: {plan_response}"""
                file_plan = request_gemini_to_generate(file_plan_prompt)

                #Creates code for the specific file using the plan.
                file_code_prompt = f"""{role}\n\n{task}\n\n Create the code for: "{file_name}" by following this guide:\n\n{file_plan}\n\nReturn only code. No explanations needed\n\n\nThe user has also requested that you draw inspiration and functions from the code snippets provided to guide you to make a solid structure: {codesnippetstext} If there is no code snippets just continue anyway as this is just a guide to help if needed."""
                code = request_gemini_to_generate(file_code_prompt)


                f.write(code)
        except Exception as e:
            print(f"Error creating file {file_name}: {e}")
            print(f"File context not available yet for {file_name}")

    #error_handling(folder_name,clean_file_names,role,task,plan_response)

def error_handling(folder_name, clean_file_names, role, task, plan_response):
    for file_name in clean_file_names:
        file_path = os.path.join(folder_name, file_name)
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()

                # Create a prompt for error correction
                file_content_prompt = f"""{role}\n\n{task}\n\nAnalyze the following code for errors and provide a corrected version. 
                You should follow the plan in this document: {plan_response} 

                ```python
                {file_content}
                ```

                Return only the corrected code. No explanations needed
                """
                corrected_file = request_gemini_to_generate(file_content_prompt)

                # Overwrite the file with the corrected code
                with open(file_path, 'w') as f:
                    f.write(corrected_file)

        except Exception as e:
            print(f"Error handling file {file_name}: {e}")

if __name__ == "__main__":
  if len(sys.argv) > 1:
    agent_data_str = sys.argv[1]
    agent_data = json.loads(agent_data_str)
    generate_plan(agent_data)
  else:
    print("No agent data received.")