import google.generativeai as genai
import dotenv
import os
import pyautogui
import re
from PIL import Image, ImageDraw, ImageFont

dotenv.load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Set up the model
generation_config = {
  "temperature": 0.1,
  "top_p": 0.95,
  "top_k": 32,
  "max_output_tokens": 1024,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# Get user input **Example**
task = input("Enter your task: ") 

# Take a screenshot at half resolution
screenshot = pyautogui.screenshot()
screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2)) 

# Draw a grid with labeled coordinates in the center of each square
grid_size = 55  # Adjust grid size as needed
draw = ImageDraw.Draw(screenshot)
font = ImageFont.truetype("arial.ttf", 8)  # Choose a font you have installed

# Draw the grid, starting at 0,0 even if not visible in the screenshot
for x in range(0, 1920, grid_size):  # Use 1920 for width
    for y in range(0, 1080, grid_size):  # Use 1080 for height
        # Calculate top-left coordinates of the grid square
        top_left_x = x
        top_left_y = y
        # Draw coordinates in semi-transparent cyan at the top-left 
        draw.text((top_left_x, top_left_y), f"({x},{y})", fill="red", font=font, anchor="la")  # 128 is about 50% opacity

# Draw the grid lines in soft cyan (thin lines)
for x in range(0, 1920, grid_size):
    draw.line([(x, 0), (x, 1080)], fill="#90e0ef", width=1)  # Soft cyan with a thin width

for y in range(0, 1080, grid_size):
    draw.line([(0, y), (1920, y)], fill="#90e0ef", width=1)  # Soft cyan with a thin width

# Save the image with the grid
image_path = "screenshot_grid.png"
screenshot.save(image_path)

uploaded_image = genai.upload_file(image_path)


# Get the actual screen resolution (we'll use this for pixel count)
screen_width, screen_height = pyautogui.size() 

# Calculate Pixel Count Directly
width_pixels = screen_width
height_pixels = screen_height
print(f"Total Pixels: ({width_pixels}, {height_pixels})")

# Divide screen resolution by 2 for prompt
half_screen_width = screen_width // 2
half_screen_height = screen_height // 2

object_location_prompt = [
    task,  
    "Image: ",
    uploaded_image,  
    f"The image is {half_screen_width} pixels wide and {half_screen_height} pixels high. This is a half-resolution version of the user's screen with a grid overlay.",
    "The grid squares have cyan coordinates in the top left corner in each cell, representing the actual screen coordinates. I need you to look at the image and tell me the coordinates of the grid square closest to the center of the object you find. If the object ocupies multiple cells. find the coordinate that might reside in between them",
    f"Using the user's request, find the '{task}' in the image. Be precise and take your time to analyze the complete image. **Don't try to calculate the coordinates, just tell me the coordinates from the grid that are closest to the object.**",
    "**Provide ONLY the coordinates from the grid in the format: '(x,y)'  (For example: '(400,200)')**" 
]
response_location = model.generate_content(object_location_prompt)

# Extract coordinates 
coordinates_text = response_location.text

# Try to find coordinates in different formats
match = re.search(r"\((?P<x>-?\d+),\s*(?P<y>-?\d+)\)", coordinates_text)

if match:
    x = int(match.group('x'))
    y = int(match.group('y'))
    print(f"Gemini Coordinates: ({x}, {y})")  # Note: No need to double x and y here

    # Move cursor to the adjusted coordinates
    pyautogui.moveTo(x*2, y*2, duration=0.5)
    pyautogui.click()
else:
    print("Coordinates still not found. Check Gemini's response:")
    print(coordinates_text)

print(response_location.text)