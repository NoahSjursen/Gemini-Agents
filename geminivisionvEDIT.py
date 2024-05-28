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

# Get actual screen resolution
screen_width, screen_height = pyautogui.size() 

# Calculate Pixel Count Directly
width_pixels = screen_width
height_pixels = screen_height
print(f"Total Pixels: ({width_pixels}, {height_pixels})")

# Divide screen resolution by 2 for prompt
half_screen_width = screen_width // 2
half_screen_height = screen_height // 2
task = input("Enter your task (or type 'exit' to quit): ")
while True:
    # Get user input
    if task == 'exit':
        break

    # Take a screenshot at half resolution
    screenshot = pyautogui.screenshot()
    screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2))

    # Draw the grid with coordinates
    grid_size = 44
    draw = ImageDraw.Draw(screenshot)
    font = ImageFont.truetype("arial.ttf", 10)
    for x in range(0, 1920, grid_size):
        for y in range(0, 1080, grid_size):
            draw.text((x, y), f"({x},{y})", fill="red", font=font, anchor="la")

    for x in range(0, 1920, grid_size):
        draw.line([(x, 0), (x, 1080)], fill="#90e0ef", width=1)

    for y in range(0, 1080, grid_size):
        draw.line([(0, y), (1920, y)], fill="#90e0ef", width=1)

    # Save the image
    image_path = "screenshot_grid.png"
    screenshot.save(image_path)

    # Upload the image
    uploaded_image = genai.upload_file(image_path)

    # Image reasoning prompt
    image_reasoning_prompt = [
        task,
        "Image: ",
        uploaded_image,
        f"Analyze this image and provide a logical response for the next steps to take. If you get multiple answers, decide the one you're most confident in and return only that answer. in the format (find: 'object') the object can be anything that you decide. but descibe it clearly with what colour, shape, text, or icons, buttons are used"
    ]
    image_reasoning = model.generate_content(image_reasoning_prompt)
    image_reasoning = image_reasoning.text
    print(image_reasoning)
    # Object location prompt
    object_location_prompt = [
        task,
        image_reasoning,
        "Image: ",
        uploaded_image,
        f"The image is {half_screen_width} pixels wide and {half_screen_height} pixels high. This is a half-resolution version of the user's screen with a grid overlay.",
        "The grid squares have red coordinates in the top left corner in each cell, representing the actual screen coordinates. If you want to choose a value but see that it is outside the boundaries of the object, try adjusting and come up with a custom value that is closer to the target than the value in the grid.",
        f"Using the user's request, {image_reasoning} the in the image. Be precise and take your time to analyze the complete image. If you are not instructed to find a specific item, try reasoning what the next logical step would be and find the object to find the coordinates for. **Don't try to calculate the coordinates, just tell me the coordinates from the grid that are closest to the object.**",
        "**Provide ONLY the coordinates from the grid in the format: '(x,y)'  (For example: '(400,200)')**"
    ]
    response_location = model.generate_content(object_location_prompt)

    # Extract coordinates
    coordinates_text = response_location.text
    match = re.search(r"\((?P<x>-?\d+),\s*(?P<y>-?\d+)\)", coordinates_text)

    if match:
        x = int(match.group('x'))
        y = int(match.group('y'))
        print(f"Gemini Coordinates: ({x}, {y})")

        # Move cursor to the adjusted coordinates
        pyautogui.moveTo(x * 2, y * 2, duration=0.5)
        pyautogui.click()
    else:
        print("Coordinates still not found. Check Gemini's response:")
        print(coordinates_text)

    print(response_location.text)