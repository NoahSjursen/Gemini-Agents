import json
import os
import subprocess







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

import os
import json







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

  while True:
    add_snippets = input("Add/Remove code snippets? (y/n): ")
    if add_snippets.lower() == 'y':
      codesnippets_dir = "codesnippets"
      if not os.path.exists(codesnippets_dir):
        print("No code snippets available.")
      else:
        print("Available Code Snippets:")
        snippets = []
        for filename in os.listdir(codesnippets_dir):
          if filename.endswith(".json"):
            snippets.append(filename)
            print(f"{len(snippets)}. {filename}")

        if snippets:
          while True:
            try:
              choice = int(input("Select code snippet (enter number, or 0 to remove): "))
              if choice == 0:
                if "codesnippets" in agent_data:
                  print("Current snippets:")
                  for i, snippet in enumerate(agent_data["codesnippets"]):
                    print(f"{i+1}. {snippet}")
                  while True:
                    try:
                      remove_choice = int(input("Enter number of snippet to remove (or 0 to cancel): "))
                      if 1 <= remove_choice <= len(agent_data["codesnippets"]):
                        del agent_data["codesnippets"][remove_choice-1]
                        print(f"Snippet '{snippets[remove_choice-1]}' removed.")
                        break
                      elif remove_choice == 0:
                        break
                      else:
                        print("Invalid choice. Please try again.")
                    except ValueError:
                      print("Invalid input. Please enter a number.")
                else:
                  print("No code snippets associated with this agent.")
                break
              elif 1 <= choice <= len(snippets):
                selected_snippet = snippets[choice - 1]
                if "codesnippets" not in agent_data:
                  agent_data["codesnippets"] = []
                agent_data["codesnippets"].append(selected_snippet)
                print(f"Code snippet '{selected_snippet}' added to agent.")
                break
              else:
                print("Invalid choice. Please try again.")
            except ValueError:
              print("Invalid input. Please enter a number.")
    else:
      break

  with open(filepath, "w") as f:
    json.dump(agent_data, f, indent=4)

  print(f"Agent '{agent_name}' updated successfully.")







def create_agent():
  """Prompts the user to enter agent details and creates a JSON file."""
  agents_dir = "agents"
  os.makedirs(agents_dir, exist_ok=True)  # Create "agents" folder if it doesn't exist

  choice = input("Create agent from scratch (s) or in an assigned folder (f)? ")

  if choice.lower() == 's':
    name = input("Enter agent name: ")
    task = input("Enter agent task: ")
    role = input("Enter agent role: ")

    agent_data = {"task": task, "role": role, "codesnippets": [""], "folder": None}  # Add "folder" key
    filename = f"{name}.json"
    filepath = os.path.join(agents_dir, filename)

    with open(filepath, "w") as f:
      json.dump(agent_data, f, indent=4)

    print(f"Agent '{name}' with task '{task}' and role '{role}' created successfully.")
  elif choice.lower() == 'f':
    folder_name = input("Enter the name of the folder: ")
    folder_path = os.path.join(agents_dir, folder_name)  # Get the folder path

    name = input("Enter agent name: ")
    task = input("Enter agent task: ")
    role = input("Enter agent role: ")

    agent_data = {"task": task, "role": role, "codesnippets": [""], "folder": folder_name}  # Add "folder" key
    filename = f"{name}.json"
    filepath = os.path.join(agents_dir, filename)  # Agent file still in "agents" folder

    with open(filepath, "w") as f:
      json.dump(agent_data, f, indent=4)

    print(f"Agent '{name}' with task '{task}' and role '{role}' created successfully. The agent is located in the 'agents' folder, and the folder name '{folder_name}' is stored in the agent's data.")
  else:
    print("Invalid choice. Please enter 's' or 'f'.")








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








def addCodeSnippets():
  """Allows users to add code snippets to the agent's knowledge base."""
  codesnippets_dir = "codesnippets"
  os.makedirs(codesnippets_dir, exist_ok=True)
  while True:
    print("\nAdd Code Snippets:")
    print("1. Paste Code")
    print("2. Paste File Path")
    print("3. Paste Folder Path")
    print("4. Back")

    choice = input("Enter your choice (1-4): ")

    if choice == '1':
      code = input("Paste your code:\n")
      filename = input("Enter a filename for the code snippet: ")
      filepath = os.path.join(codesnippets_dir, filename + ".json")
      with open(filepath, 'w') as f:
        json.dump({"code": f"```python\n{code}\n```"}, f, indent=4)
      print("Code snippet added successfully.")

    elif choice == '2':
      filepath = input("Enter the file path: ")
      if os.path.exists(filepath):
        with open(filepath, 'r') as f:
          code = f.read()
        filename = os.path.basename(filepath).split(".")[0] + ".json"
        filepath = os.path.join(codesnippets_dir, filename)
        with open(filepath, 'w') as f:
          json.dump({"code": f"```python\n{code}\n```"}, f, indent=4)
        print("Code snippet added successfully.")
      else:
        print("Invalid file path. Please try again.")

    elif choice == '3':
      folder_path = input("Enter the folder path: ")
      if os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
          if filename.endswith((".py", ".txt")):  # Assuming Python or text files
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as f:
              code = f.read()
            output_filename = filename.split(".")[0] + ".json"
            output_filepath = os.path.join(codesnippets_dir, output_filename)
            with open(output_filepath, 'w') as f:
              json.dump({"code": f"```python\n{code}\n```"}, f, indent=4)
        print("Code snippets from the folder added successfully.")
      else:
        print("Invalid folder path. Please try again.")

    elif choice == '4':
      break
    else:
      print("Invalid choice. Please try again.")








while True:
  print("\nAgent Management System:")
  print("1. View Agents")
  print("2. Create Agent")
  print("3. Exit")
  print("4. Add Code Snippets")

  choice = input("Enter your choice (1-3): ")

  if choice == '1':
    view_agents()
  elif choice == '2':
    create_agent()
  elif choice == '3':
    print("Exiting...")
    break
  elif(choice == '4'):
    addCodeSnippets()
  else:
    print("Invalid choice. Please try again.")