import json
import os
import subprocess
import dotenv
import google.generativeai as genai

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



def view_agents():
  """Displays a list of agents in the 'agents' folder and allows selection."""
  print("Available Agents:")
  agents_dir = "agents"
  if not os.path.exists(agents_dir):
    print("No agents available.")
    return

  agents = []
  for filename in os.listdir(agents_dir):
    if filename.endswith(".json"):
      agent_name = filename[:-5]  # Remove ".json" from filename
      with open(os.path.join(agents_dir, filename), "r") as f:
        agent_data = json.load(f)
      agents.append((agent_name, agent_data))
      print(f"{len(agents)}. {agent_name} - Task: {agent_data['task']}, Role: {agent_data['role']}")

  if agents:
    while True:
      try:
        choice = int(input("Select an agent (enter number): "))
        if 1 <= choice <= len(agents):
          selected_agent, agent_data = agents[choice - 1]
          agent_action(selected_agent, agent_data)
          break
        else:
          print("Invalid choice. Please try again.")
      except ValueError:
        print("Invalid input. Please enter a number.")

def agent_action(agent_name, agent_data):
  """Provides actions to perform on the selected agent."""
  while True:
    print(f"\nActions for '{agent_name}':")
    print("1. Start")
    print("2. Stop")
    print("3. Edit")
    print("4. Delete")  # Add delete option
    print("5. Back")

    choice = input("Enter your choice (1-5): ")  # Update choice range

    if choice == '1':
      start_agent(agent_name, agent_data)
    elif choice == '2':
      print(f"Stopping agent '{agent_name}'...")
      # TODO: Implement stop logic
    elif choice == '3':
      edit_agent(agent_name, agent_data)
    elif choice == '4':
      delete_agent(agent_name)  # Call delete function
    elif choice == '5':
      break
    else:
      print("Invalid choice. Please try again.")

def edit_agent(agent_name, agent_data):
  """Edits the details of the selected agent."""
  agents_dir = "agents"
  filepath = os.path.join(agents_dir, f"{agent_name}.json")

  print(f"\nEditing agent '{agent_name}':")
  print(f"Current task: {agent_data['task']}")
  print(f"Current role: {agent_data['role']}")

  new_task = input("Enter new task (leave blank to keep current): ")
  new_role = input("Enter new role (leave blank to keep current): ")

  if new_task:
    agent_data["task"] = new_task
  if new_role:
    agent_data["role"] = new_role

  with open(filepath, "w") as f:
    json.dump(agent_data, f, indent=4)

  print(f"Agent '{agent_name}' updated successfully.")

def create_agent():
  """Prompts the user to enter agent details and creates a JSON file."""
  agents_dir = "agents"
  os.makedirs(agents_dir, exist_ok=True)  # Create "agents" folder if it doesn't exist

  name = input("Enter agent name: ")
  task = input("Enter agent task: ")
  role = input("Enter agent role: ")

  agent_data = {"task": task, "role": role}
  filename = f"{name}.json"
  filepath = os.path.join(agents_dir, filename)

  with open(filepath, "w") as f:
    json.dump(agent_data, f, indent=4)

  print(f"Agent '{name}' with task '{task}' and role '{role}' created successfully.")


def start_agent(agent_name, agent_data):
  """Starts the agent by sending data to the agent_script.py"""
  print(f"Starting agent '{agent_name}'...")

  # Pass agent_data as a JSON string to agent_script.py
  process = subprocess.run(
    ["python", "agent.py", json.dumps(agent_data)], 
    capture_output=True, text=True
  )
  print(process.stdout)  # Print output from agent_script.py
  print(process.stderr)  # Print potential errors from agent_script.py

  print(f"Agent '{agent_name}' started.")

def delete_agent(agent_name):
  """Deletes the selected agent."""
  agents_dir = "agents"
  filepath = os.path.join(agents_dir, f"{agent_name}.json")

  if os.path.exists(filepath):
    os.remove(filepath)
    print(f"Agent '{agent_name}' deleted successfully.")
  else:
    print(f"Agent '{agent_name}' not found.")

while True:
  print("\nAgent Management System:")
  print("1. View Agents")
  print("2. Create Agent")
  print("3. Exit")

  choice = input("Enter your choice (1-3): ")

  if choice == '1':
    view_agents()
  elif choice == '2':
    create_agent()
  elif choice == '3':
    print("Exiting...")
    break
  else:
    print("Invalid choice. Please try again.")