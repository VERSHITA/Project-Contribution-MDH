import tkinter as tk
import cv2
import threading
from PIL import Image, ImageTk
import customtkinter as ckt
import csv
import os
from datetime import datetime
import pytz
import tkinter.font as tkfont

root = ckt.CTk()
ckt.set_appearance_mode("System")
ckt.set_default_color_theme("green")


def update_log(message):
    log_text.config(state=tk.NORMAL)  # Allow editing
    log_text.insert(tk.END, str(message) + "\n")
    log_text.config(state=tk.DISABLED)  # Disable editing
    log_text.yview(tk.END)

# Flag to control video processing
is_processing = False
cap = None
time1=0
time2=0
count1=0



def start_video_processing():
    utc_now = datetime.now(pytz.utc)
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = utc_now.astimezone(ist)
    

    global is_processing, cap, count1,time1
    time1= ist_now.strftime('%Y-%m-%d %H:%M:%S')
    videopath = camera_link_entry.get()  # Get the camera link from the input box
    #update_log(videopath)
    is_processing = True

    # Open the video file
    cap = cv2.VideoCapture(videopath)
    #update_log(cap.isOpened())
    # Check if the video file opened successfully
    if not cap.isOpened():
        update_log("Error: Could not open video file.")
        return
    print("cap=", cap.isOpened())
    # Create background subtractor object
    object_detector = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=100)

    # Flag to indicate whether the object has been counted in the current crossing
    counted = False

    # Line position for counting
    # Adjust this based on your ROI height
    
    while is_processing:
        # Read a frame from the video
        ret, frame = cap.read()
        if ret==False:
            update_log("End of video.")
        if frame==[ ]:
            update_log("Frame is not Capturing.")

        
        # Define the region of interest (ROI)
        roi = frame[150:576, 350:550]
        
        if roi.size == 0:
            update_log("ROI is empty. Skipping this frame.")
            continue
      
        # Convert to RGB before displaying
        try:
            roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            update_log(f"Error converting frame to RGB: {e}")
            continue

        # Apply background subtraction on the ROI
        mask = object_detector.apply(roi)

        # Apply binary thresholding to the mask
        _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Variable to store the largest contour
        largest_contour = None
        largest_area = 0
        line_position1 = 90
        line_position2 = 400
        # Draw the counting lines
        start_point1 = (0, line_position1)  # Starting from the left edge at y=line_position1
        end_point1 = (roi.shape[1], line_position1)  # End point within ROI
        start_point2 = (0, line_position2)  # Starting from the left edge at
        end_point2 = (roi.shape[1], line_position2)  # End point within
        cv2.line(roi, start_point1, end_point1, (255, 0, 0), 3)
        cv2.line(roi, start_point2, end_point2, (255, 0, 0), 3)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:  # Adjust this value based on your input video
                if area > largest_area:
                    largest_area = area
                    largest_contour = cnt

        # Draw the largest contour if found
        if largest_contour is not None:
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(roi, (center_x, center_y), 2, (0, 0, 255), -1)

            # Print debugging information
            update_log(f"Center Y: {center_y}, Line Position1: {line_position1}, Counted: {counted}")
            

            # Check if the center of the contour crosses the line
            if (line_position1 + 20) < center_y < (line_position2 - 10) and not counted:
                count1 += 1
                counted = True
                update_log(f"Count increased to {count1}")
                update_log(f"Center Y: {center_y}, Line Position1: {line_position1}, Counted: {counted}")
            elif center_y <= line_position1 or center_y >= line_position2:
                counted = False
                update_log(f"Center Y: {center_y}, Line Position1: {line_position1}, Counted: {counted}")

        cv2.putText(roi, f'Count: {count1}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)

        # Convert the frame to an image and display it in Tkinter
        try:
            roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(roi_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the video_label with the new image
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
            video_label.update_idletasks()
        except cv2.error as e:
            update_log(f"Error displaying frame: {e}")
            continue

        # Display the frames
        #cv2.imshow('ROI', roi)
        #cv2.imshow('Mask', mask)
        


        # Break the loop if the user presses the 'q' key
        if cv2.waitKey(10) & 0xFF == ord('q'):
            update_log("Video is Closed.")
            break

    cap.release()
    cv2.destroyAllWindows()

def stop_video_processing():
    global is_processing, cap,time2
    utc_now = datetime.now(pytz.utc)
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = utc_now.astimezone(ist)
    is_processing = False
    if cap is not None:
        cap.release()
        cv2.destroyAllWindows()
        time2=ist_now.strftime('%Y-%m-%d %H:%M:%S')
        update_log("Video is Closed.")

def start_thread():
    threading.Thread(target=start_video_processing).start()

def csv_file():
    if csv_file_entry.get()=="":
        update_log("Please select a csv file")
        return
    file_exists = os.path.isfile(csv_file_entry.get())
    if file_exists==True:
        file=open(csv_file_entry.get(),"a",newline="\n")
        csvFile = csv.writer(file)
        listt=[time1,time2,count1]
        csvFile.writerow(listt)
        file.close()
        update_log("File created.")
    else:
        file=open(csv_file_entry.get(),"w",newline="\n")
        csvFile = csv.writer(file)
        csvFile.writerow([time1,time2,count1])
        file.close()
        update_log("File created.")
        


# GUI setup
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
title_font = tkfont.Font(family="Times Roman", size=40, weight="bold")
title_label = tk.Label(root, text="Boxes Counting Application ", font=title_font)
title_label.pack(pady=10) 
root.geometry(f"{screen_width}x{screen_height}")

label = ckt.CTkLabel(root, text="This is a box-counting application. Enter the RTSP link of the camera in the provided field, then specify the name of the CSV file (e.g., file.csv). The application will count the boxes and record the time duration, saving the data to the specified CSV file on your local PC. Use the Start and Stop buttons to control the box counting, and click the CSV button at the end to generate the CSV file.", wraplength=1000, font=('Arial', 20))
label.pack()

camera_link_frame = ckt.CTkFrame(root)
camera_link_frame.pack(pady=20)

camera_link_label = ckt.CTkLabel(camera_link_frame, text="Enter the camera link:", font=("Helvetica", 18))
camera_link_label.pack(side=tk.LEFT, padx=10)

camera_link_entry = tk.Entry(camera_link_frame, font=("Helvetica", 18), width=50)
camera_link_entry.pack(side=tk.LEFT)

csv_file_frame = ckt.CTkFrame(root)
csv_file_frame.pack(pady=20)

csv_file_label = ckt.CTkLabel(csv_file_frame, text="Enter the CSV file name:", font=("Helvetica", 18))
csv_file_label.pack(side=tk.LEFT, padx=10)

csv_file_entry = tk.Entry(csv_file_frame, font=("Helvetica", 18), width=50)
csv_file_entry.pack(side=tk.LEFT)

button_frame = ckt.CTkFrame(root)
button_frame.pack(pady=20)

start_button = ckt.CTkButton(button_frame, text="Start", font=("Helvetica", 18), command=start_thread)
start_button.pack(side=tk.LEFT, padx=30)

stop_button = ckt.CTkButton(button_frame, text="Stop", font=("Helvetica", 18), command=stop_video_processing)
stop_button.pack(side=tk.LEFT, padx=30)

csv_button = ckt.CTkButton(button_frame, text="CSV", font=("Helvetica", 18), command=csv_file)
csv_button.pack(side=tk.LEFT, padx=30)

log_frame = tk.Frame(root)
log_frame.pack(anchor='w')

log_text = tk.Text(log_frame, height=30, width=40, font=("Helvetica", 12), wrap=tk.WORD, state=tk.DISABLED)
log_text.pack(side=tk.LEFT, padx=(300, 350))

video_frame = tk.Frame(log_frame)
video_frame.pack(side=tk.RIGHT, pady=0)  # Position at the bottom with padding

video_label = ckt.CTkLabel(video_frame, text="", height=500, width=800)
video_label.pack(padx=0, pady=0)

count_frame = tk.Frame(video_frame)
count_frame.pack(side=tk.TOP, pady=100)  # Changed to TOP for better alignment

# Initialize count_var
count_var = tk.StringVar()
count_var.set("0")  # Default value for the counter

count_label = ckt.CTkLabel(count_frame, textvariable=count_var, height=10, width=10, font=("Arial", 24))
count_label.pack(side=tk.TOP, pady=100)  # Changed to TOP for better alignment

root.mainloop()
#vid.mp4