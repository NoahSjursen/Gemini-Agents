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

def generate_plan_and_files(agent_data):
    task = agent_data['task']
    role = agent_data['role']

    # Construct a prompt for the AI to generate a detailed plan
    prompt = f"""
    You are a "{role}" tasked with "{task}".
    The task should be completed as a single solution. not multiple projects.
    Input: [Describe the input data format]
    Output: [Describe the desired output format]
    Constraints: [Specify any limitations]
    Evaluation Criteria: [List criteria for assessing the plan]
    Error Handling: [Mention the need to address potential errors]
    When importing libraries make sure you import all needed components of that library. And make sure they are all used.
    ## File Structure and Responsibilities:

    Design a logical file structure for this project. For each file you create, clearly state its purpose and the specific tasks it will handle.

    **Example:**

    **File: `[filename]`**
    * Purpose:  [purpose].
    * Tasks:
        [tasks]
        [tasks]

    **Provide a detailed plan for each file.**

    ## Plan:
    [Write your detailed plan here, including specific steps for each file.]
    """

    response = request_gemini_to_generate(prompt)

    # Analyze the plan to extract file names
    file_names = []
    prompt_filenames = f"You are tasked with finding the files required in this project. look for text with 'Create a file named: 'filename' ' for each file you find. add to a list with filenames only seperated by comma. here is the info to look through: {response} place 'start.py' at the end of the list use no other formatting such as '' when placing into the string"
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

    # Create the folder

    # Generate a random 10-character string
    folder_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

    print(folder_name)

    os.makedirs(folder_name, exist_ok=True)

    file_context = ""
    for i, file_name in enumerate(clean_file_names):
        file_path = os.path.join(folder_name, file_name)
        try:
            with open(file_path, 'w') as f:
                # Read content of previous files
                for j in range(i):
                    previous_file_name = clean_file_names[j]
                    previous_file_path = os.path.join(folder_name, previous_file_name)
                    with open(previous_file_path, 'r') as prev_f:
                        file_context += f"## {previous_file_name}\n{prev_f.read()}\n"

                prompt = f"""{role}\n{task}\n{response}\n{file_context}## {file_name}\nMake the needed code for the specific {file_name} file. Make sure to only return code. no explanations needed since this will be input directly into a file. If you are making start.py include all imports from previous scripts so that it doesn't break"""
                code = request_gemini_to_generate(prompt)
                f.write(code)
        except Exception as e:
            print(f"Error creating file {file_name}: {e}")
            print(f"File context not available yet for {file_name}")

    file_path = os.path.join(folder_name, "start.py")
    process = subprocess.run(
        ["python", file_path], 
        capture_output=True, text=True
    )



if __name__ == "__main__":
  if len(sys.argv) > 1:
    agent_data_str = sys.argv[1]
    agent_data = json.loads(agent_data_str)
    generate_plan_and_files(agent_data)
  else:
    print("No agent data received.")