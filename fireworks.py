import tkinter as tk
import random
from PIL import Image, ImageTk

# Window setup
WIDTH, HEIGHT = 800, 600
root = tk.Tk()
root.title("Fireworks")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()

# Firework class
class Firework:
    def __init__(self):
        self.particles = []
        self.create_particles()

    def create_particles(self):
        x = random.randint(100, WIDTH-100)
        y = random.randint(100, HEIGHT-300)
        for _ in range(50):
            dx = random.uniform(-4, 4)
            dy = random.uniform(-4, 0)
            color = random.choice(["red","yellow","blue","green","purple","orange"])
            particle = {"x": x, "y": y, "dx": dx, "dy": dy, "color": color}
            self.particles.append(particle)

    def update(self):
        for p in self.particles:
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            p["dy"] += 0.1  # gravity
        self.particles = [p for p in self.particles if p["y"] < HEIGHT]

    def draw(self, canvas):
        for p in self.particles:
            canvas.create_oval(p["x"], p["y"], p["x"]+4, p["y"]+4, fill=p["color"], outline="")

fireworks = []

def animate():
    canvas.delete("all")
    if random.random() < 0.05:
        fireworks.append(Firework())
    for f in fireworks:
        f.update()
        f.draw(canvas)
    root.after(50, animate)

animate()
root.mainloop()
