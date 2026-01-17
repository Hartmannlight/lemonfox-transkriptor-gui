from tkinter import Tk

from lemonfox_gui.ui import App


def main():
    root = Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
