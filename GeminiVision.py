import google.generativeai as genai
import dotenv
import os
import pyautogui
from PIL import Image, ImageDraw, ImageFont
import re
from time import sleep
dotenv.load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Set up the model
generation_config = {
  "temperature": 0.9,
  "top_p": 0.95,
  "top_k": 32,
  "max_output_tokens": 1024,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)



def initial_screenshot():
  # Take a screenshot
  screenshot = pyautogui.screenshot()
  screenshotClean = screenshot.resize((screenshot.width // 2, screenshot.height // 2))
  screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2))

  # Draw the grid with coordinates
  grid_size = 60
  draw = ImageDraw.Draw(screenshot)
  font = ImageFont.truetype("arial.ttf", 11)

  # Iterate over each grid cell, ensuring full height coverage
  for x in range(0, screenshot.width, grid_size): 
      for y in range(0, screenshot.height, grid_size):
          # Check if the center of the cell is within the image bounds
          if x + grid_size // 2 < screenshot.width and y + grid_size // 2 < screenshot.height:
              # Get the pixel color at the center of the cell
              pixel_color = screenshot.getpixel((x + grid_size // 2, y + grid_size // 2))

              # Calculate contrasting color with 25% opacity (lighter)
              contrast_color = (255 - pixel_color[0], 255 - pixel_color[1], 255 - pixel_color[2], 64)  # Adding alpha for opacity

              # Draw the grid line with lighter opacity
              # Extend the lines to the image boundaries
              draw.line([(x, y), (x, screenshot.height)], fill=contrast_color, width=1) 
              draw.line([(x, y), (screenshot.width, y)], fill=contrast_color, width=1)

              # Draw the coordinates with lighter opacity
              draw.text((x, y), f"\n {x},{y} ", fill=contrast_color, font=font, anchor="la")


  # Save the image
  image_path = "screenshot_grid.png"
  screenshot.save(image_path)

  # Upload the image **after** saving it
  image_reasoning(image_path,screenshotClean)

def image_reasoning(image_path, screenshotClean):
    uploaded_image = genai.upload_file(image_path)

    prompt_parts = [
        "Initial task:",
        initial_task,
        "Based on this task given. Determine where you are in the process and what is next. See what applications, icons, or other guiding items you have that would logically reach the intended goal"
        "if the given task contains nothing move on and decide what you would like to do yourself.",
        uploaded_image,
        "You are an AI agent exploring a digital environment. Imagine yourself interacting with this environment.",
        "Identify the most relevant UI elements in the image (e.g., buttons, menus, text fields, icons, game elements like characters, enemies, items).", 
        "Based on these elements and their state (e.g., enabled, disabled, highlighted, active, inactive), what is the next logical step I should take to interact with this environment? ",

        "If this is a game, provide answers to the following questions:",
        "1. What game is this? ",
        "2. What are the general tasks or objectives in this game?",
        "3. Based on the current screenshot, what specific actions should I take to progress in the game? Provide a step-by-step guide for achieving this goal."

        "The return should be one task. Primarily the one object you are most confident in. Return the name of the object"
        "Also return as a seperate line: '''ACTION:(action)''' The different actions could be: \n"
        "   - '(click)': Click the object with your mouse cursor. This is usually used for selecting, highlighting, or activating an item or button.\n"
        "   - '(doubleclick)': Double-click the object with your mouse cursor. This is typically used to open files, applications, or folders, or to perform specific actions depending on the context.\n"
        "   - '(rightclick)': Right-click the object with your mouse cursor. This usually opens a context menu with additional options or actions related to the object. Can be used for creating new files, folders, properties and other stuff in applications\n"
        "   - '(type)':  Start typing text in the object. If it's a text field, you will need to provide the text content in the next line.\n" 
        "The actions should reflect what needs to be done with the item. If the image shows a typing field that is not yet activated, you can still choose option 'type'.\n" 
        "If the action is (type), then write '''CONTENT:(text you want to write here)''' You are the one who decides what the text should be. Use logic relevant to the image given." 
    ]

    task = model.generate_content(prompt_parts)
    task = task.text
    print(task)

    match = re.search(r"'''ACTION:(.*?)'''", task)

    if match:
        action = match.group(1)
        print(f"Extracted action: {action}")
    else:
        action = "(click)"
        print("No action found in the task string.")

    # Construct the prompt
    prompt_parts = [
      "Image: ",
      uploaded_image,
      f"Analyze the image. There are coordinates displayed. Look for the object specified in the task: {task}.When you find the object. Look for the coordinates displayed in the top left of that cell and return '''CELL:(x,y)''' . Also return the coordinates of the cell that is one space down and one space right '''DIAGONAL:(x,y)'''"
    ]


    # Send the prompt to Gemini
    response = model.generate_content(prompt_parts)
    print(response.text)
    crop_and_grid(response.text, screenshotClean,task, action)


def crop_and_grid(response_text, screenshotClean, task, action):
  """Crops an image, upscales it by 4 times, draws a 10x10 grid with screen coordinates.

  Args:
      response_text: The text response containing the coordinates.
      screenshotClean: The original image to be cropped.
      task: The task for image analysis.

  Returns:
      The cropped and upscaled image with the grid and numbers drawn on top.
  """

  cell_match = re.search(r"CELL:\s*\((.*?)\)", response_text)
  diagonal_match = re.search(r"DIAGONAL:\s*\((.*?)\)", response_text)

  if cell_match and diagonal_match:
    cell_coordinates = tuple(map(int, cell_match.group(1).split(",")))
    diagonal_coordinates = tuple(map(int, diagonal_match.group(1).split(",")))

    # Crop the image
    cropped_image = screenshotClean.crop(
        (cell_coordinates[0], cell_coordinates[1], diagonal_coordinates[0], diagonal_coordinates[1])
    )

    # Upscale the image by 4 times
    cropped_image = cropped_image.resize((cropped_image.width * 10, cropped_image.height * 10), Image.Resampling.LANCZOS)  # Use LANCZOS for better quality upscaling

    # Draw the grid
    draw = ImageDraw.Draw(cropped_image)
    grid_size = 5  # Number of grid cells
    cell_width = cropped_image.width // grid_size
    cell_height = cropped_image.height // grid_size

    for i in range(grid_size):
      for j in range(grid_size):
        # Calculate screen coordinates based on diagonal values
        x_screen = cell_coordinates[0] + j * (diagonal_coordinates[0] - cell_coordinates[0]) // grid_size
        y_screen = cell_coordinates[1] + i * (diagonal_coordinates[1] - cell_coordinates[1]) // grid_size
        # Draw the coordinates in the top left of the cell
        draw.text((j * cell_width + 5, i * cell_height + 5), f"({x_screen},{y_screen})", fill="cyan", font=ImageFont.truetype("arial.ttf", 16))

    for i in range(1, grid_size):
      draw.line(
          ((i * cell_width, 0), (i * cell_width, cropped_image.height)), fill="white"
      )
      draw.line(
          ((0, i * cell_height), (cropped_image.width, i * cell_height)), fill="white"
      )

    cropped_image.save("cropped_image.png")
    print("Cropped and upscaled image saved as cropped_image.png")
    get_coordinates(task, action)
  else:
    print("Could not find the coordinates in the response.")
    return None

def get_coordinates(task, action):
    image_path = "cropped_image.png"
    uploaded_image = genai.upload_file(image_path)

    prompt_parts = [
        "Image: ",
        uploaded_image,
        f"Analyze the image. There are coordinates displayed in a grid format. The grid is evenly spaced. Find the cell that is overlayed as much as possible over the object specified in the task: {task}. Then, fill in the coordinates strictly in this format '''CELL:(x,y)'''"
    ]

    response = model.generate_content(prompt_parts)  # Keep the Response object

    print(response.text)

    cell_match = re.search(r"CELL:\s*\((.*?)\)", response.text)
    if cell_match:
        coordinates_str = cell_match.group(1)
        x, y = map(int, coordinates_str.split(","))
        move_cursor(x, y, action, task)  # Call your function to move the cursor
    else:
        print("Could not find coordinates in the response.")




def move_cursor(x, y, action, task):
    """
    Moves the cursor to the specified coordinates and performs the specified action.

    Args:
        x (int): X coordinate of the target location.
        y (int): Y coordinate of the target location.
        action (str): The action to perform, one of: "(click)", "(doubleclick)", "(type)".
    """

    # Time the coordinates by 2
    x_timed = x * 2
    y_timed = y * 2

    # Move the cursor
    pyautogui.moveTo(x_timed, y_timed, duration=0.5)

    # Perform the action
    if action == "(click)":
        pyautogui.click()

    elif action == "(doubleclick)":
        pyautogui.doubleClick()

    elif action == "(type)":
        pyautogui.click()
        content_prompt = f"Based on the task given Extract the contents of '''CONTENT:(text)''' Return only the text within the (). Here is the task for refrence: {task}"
        content = model.generate_content(content_prompt)
        content = content.text
        print(content)
        pyautogui.typewrite(content)
        pyautogui.press("enter")

    elif action =="(rightclick)":
      pyautogui.rightClick()

    else:
        print("Invalid action specified.")

    screenshot = pyautogui.screenshot()
    screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2))

    image_path = "screenshot_grid.png"
    sleep(3)
    screenshot.save(image_path)


initial_task = input("Task: ")
# Get user input
while True:
  initial_screenshot()
