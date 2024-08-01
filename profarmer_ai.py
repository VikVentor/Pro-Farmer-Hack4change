import tkinter as tk
from PIL import Image, ImageTk
import random
import speech_recognition as sr
import threading
import time
import os
import google.generativeai as genai
from gtts import gTTS
import playsound
import re
import requests



# Configure the Google Gemini API with your API key
genai.configure(api_key="API KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

# ESP32 IP addresses and endpoints
soil_moisture_ip = "http://192.168.37.99"
ldr_co2_ip = "http://192.168.37.166"
soil_moisture_endpoint = '/'
control_endpoint = '/control'
ldr_endpoint = '/ldr'
co2_endpoint = '/co2'

# Function to clean the response text
def clean_response_text(text):
    # Remove special characters such as asterisks
    text = re.sub(r'[^\w\s,.?!]', '', text)
    return text

# Function to call the Google Gemini API using the updated method
def get_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        # Clean and truncate the response
        max_length = 200
        cleaned_response = clean_response_text(response.text)
        if len(cleaned_response) > max_length:
            cleaned_response = cleaned_response[:max_length].rsplit(' ', 1)[0] + "..."
        return cleaned_response
    except Exception as e:
        return f"Error: {str(e)}"

# Function to vocalize the response using gTTS
def speak_response(response):
    try:
        # Create a gTTS object
        tts = gTTS(text=response, lang='en', slow=True)
        # Save the audio file
        audio_file = "response.mp3"
        tts.save(audio_file)
        # Play the audio file
        playsound.playsound(audio_file)
    except Exception as e:
        print(f"Error with text-to-speech: {e}")

# Function to get soil moisture data from the ESP32
def get_soil_moisture_data():
    try:
        response = requests.get(soil_moisture_ip + soil_moisture_endpoint)
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to get soil moisture data. Status code: {response.status_code}"
    except Exception as e:
        return f"Error occurred: {e}"

# Function to get LDR and CO2 data from the ESP32
def get_ldr_co2_data():
    try:
        ldr_response = requests.get(ldr_co2_ip + ldr_endpoint)
        co2_response = requests.get(ldr_co2_ip + co2_endpoint)
        if ldr_response.status_code == 200 and co2_response.status_code == 200:
            return f"{ldr_response.text}"
        else:
            return f"Failed to get LDR or CO2 data. Status code: LDR={ldr_response.status_code}, CO2={co2_response.status_code}"
    except Exception as e:
        return f"Error occurred: {e}"

# Function to control the relay on the ESP32
def control_relay(state):
    try:
        response = requests.post(soil_moisture_ip + control_endpoint, data={'state': state})
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to control relay. Status code: {response.status_code}"
    except Exception as e:
        return f"Error occurred: {e}"

# Function to create a question based on sensor data
def create_agriculture_question(sensor_data):
    question = f"The sensor data shows {sensor_data}. Tell in one line how this data affects my crop."
    return question

# Function to create the main window and display the background image
def create_window_with_background():
    # Create the main window
    root = tk.Tk()
    root.title("Fullscreen Background Image")

    # Set the window to fullscreen
    root.attributes('-fullscreen', True)

    # Create a Canvas widget to draw the background image and shapes
    canvas = tk.Canvas(root, bg='white', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)  # Make the canvas fill the entire window

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Load and display the background image
    bg_image = Image.open("agris.png")
    bg_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)  # Resize image to fit window
    bg_photo = ImageTk.PhotoImage(bg_image)
    canvas.create_image(0, 0, anchor='nw', image=bg_photo)

    # Define font and color for the text
    font = ('Bodoni MT', 15, "bold")
    color = 'white'
    font1 = ('Bodoni MT', 10, "italic")

    # Parameters for the visualizer bars
    num_bars = 10
    bar_width = 20
    bar_spacing = 10
    bar_x_start = 1500  # Position visualizer near the text
    bar_y_start = 800
    max_bar_height = 100

    # Create visualizer bars
    bars = []
    for i in range(num_bars):
        bar_x = bar_x_start + i * (bar_width + bar_spacing)
        bar = canvas.create_rectangle(bar_x, bar_y_start, bar_x + bar_width, bar_y_start - max_bar_height, fill='white')
        bars.append(bar)

    visualizer_running = False

    # Function to update the visualizer bars
    def update_visualizer():
        if visualizer_running:
            for bar in bars:
                new_height = random.randint(20, max_bar_height)
                canvas.coords(bar, canvas.coords(bar)[0], bar_y_start, canvas.coords(bar)[2], bar_y_start - new_height)
            root.after(100, update_visualizer)  # Schedule next update

    # Function to start the visualizer
    def start_visualizer():
        nonlocal visualizer_running
        visualizer_running = True
        update_visualizer()
        root.after(5000, stop_visualizer)  # Stop the visualizer after 5 seconds

    # Function to stop the visualizer
    def stop_visualizer():
        nonlocal visualizer_running
        visualizer_running = False

    # Function to listen for questions and fetch Gemini response
    def listen_for_question():
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        while True:
            with microphone as source:
                print("Listening for question...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
                


            try:
                question = recognizer.recognize_google(audio).lower()
                print(f"Question: {question}")

                # Calculate center of the canvas
                
                center_x = 900
                center_y = 900

                if "data" in question:
                    # Fetch and display data from both ESP32s
                    start_visualizer
                    soil_moisture_data = get_soil_moisture_data()
                    ldr_co2_data = get_ldr_co2_data()
                    print(f"{soil_moisture_data}")
                    print(f"{ldr_co2_data}")

                    canvas.delete('answer')

                    # Clear previous sensor data text
                    canvas.delete('sensor_data')

                    # Display sensor data on the canvas
                    canvas.create_text(700, 1100, text=f"{soil_moisture_data}", font=font, fill=color, anchor='center', tags='sensor_data')
                    canvas.create_text(center_x, center_y, text=f"{ldr_co2_data}", font=font, fill=color, anchor='center', tags='sensor_data')

                    # Formulate the question for Gemini
                    agriculture_question = create_agriculture_question(soil_moisture_data + ldr_co2_data)
                    print(f"Formulated Question: {agriculture_question}")

                    # Get response from Google Gemini
                    answer = get_gemini_response(agriculture_question)
                    print(f"Answer: {answer}")

                    # Clear previous answer text
                    canvas.delete('answer')

                    # Display answer on the canvas
                    canvas.create_text(2300, 500 , text=f"Answer: {answer}", font=font1, fill=color, anchor='e', tags='answer')

                    # Vocalize the sensor data and the Gemini response
                    speak_response(f"{answer}")

                elif "relay on" in question:
                    canvas.delete('relay')
                    # Turn the relay on
                    response = control_relay("on")
                    print(response)
                    canvas.create_text(1000, 1350 , text=f"Irrigating ON", font=font, fill=color, anchor='ne', tags='relay')
                    speak_response("watering is on.")
                    
                elif "relay off" in question or "relay of" in question:
                    canvas.delete('relay')
                    # Turn the relay off
                    response = control_relay("off")
                    print(response)
                    canvas.create_text(1000, 1350 , text=f"Irrigating OFF", font=font, fill=color, anchor='ne', tags='relay')
                    speak_response("watering is off.")

                else:
                    # Get response from Google Gemini
                             
                    # Get response from Google Gemini for other questions
                    response = get_gemini_response(question)
                    print(f"Answer: {response}")

                    # Clear previous answer text
                    canvas.delete('answer')

                    # Display answer on the canvas
                    canvas.create_text(center_x, center_y, text=f"Answer: {response}", font=font, fill=color, anchor='center', tags='answer')

                    # Vocalize the response
                    speak_response(response)

            except sr.UnknownValueError:
                print("Sorry, I did not understand the audio.")
            except sr.RequestError as e:
                print(f"Error with speech recognition service: {e}")

    # Start the speech recognition thread
    threading.Thread(target=listen_for_question, daemon=True).start()

    # Start the visualizer when the application starts
    start_visualizer()

    # Start the main event loop
    root.mainloop()

# Run the application
create_window_with_background()
