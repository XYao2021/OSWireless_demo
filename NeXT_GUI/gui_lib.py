#######################################################
# Author: Zhangyu Guan
#######################################################

from tkinter import *
import tkinter as tk
from PIL import ImageTk, Image

#######################################################
# Create a window and maximize it
#######################################################
root = Tk()
root.state("zoomed")
root.title("UB NeXT - Next Optimization, Emulation and Deployment System")

#######################################################
# Create a canvas
#######################################################

cw, ch = root.winfo_screenwidth(), root.winfo_screenheight()
chart_1 = Canvas(root, width=cw/2, height=ch, background= "white")
cycle_period = 200 # time between fresh positions of the ball
# (milliseconds).
# The parameters determining the dimensions of the ball and it’s
# position.
posn_x = 1 # x position of box containing the ball (bottom).
posn_y = 1 # y position of box containing the ball (left edge).
shift_x = 3 # amount of x-movement each cycle of the ‘for’ loop.
shift_y = 3 # amount of y-movement each cycle of the ‘for’ loop.
ball_width = 12 # size of ball – width (x-dimension).
ball_height = 12 # size of ball – height (y-dimension).
color = "purple" # color of the ball
chart_1.pack(side=tk.RIGHT)
testbed = ImageTk.PhotoImage(file="testbed.jpg")
chart_1.create_image(0, 0, image = testbed, anchor =  NW)

#######################################################
# Create text window
#######################################################
text2 = tk.Text(root, font = 10, height=40, width= 140)
text2.place(x=0,y=0)
scroll = tk.Scrollbar(root, command=text2.yview)
text2.configure(yscrollcommand=scroll.set)
text2.tag_configure('bold_italics', font=('Arial', 12, 'bold', 'italic'))
text2.tag_configure('big', font=('Verdana', 10, 'bold'))
text2.tag_configure('color', foreground='#476042', font=('Tempus Sans ITC', 12, 'bold'))
text2.insert(tk.END,'\nWilliam Shakespeare\n', 'big')

#######################################################
# Another text window
#######################################################
text3 = tk.Text(root, font = 10, height=40, width=140)

text3.place(x=0,y=ch/2+10)

def callback(event):
    item = chart_1.find_closest(event.x, event.y)
    text2.delete('1.0', END)
    text2.insert(tk.END, item)


color = "white" # color of the ball
x = 400
y = 100    
chart_1.create_oval(x, y, x + 50, y + 50, fill = color) 

color = "red" # color of the ball
x = 470
y = 700    
chart_1.create_oval(x, y, x + 50, y + 50, fill = color)  

chart_1.bind("<Button-1>", callback) 
    
root.mainloop()