import rumps
class App(rumps.App):
    def __init__(self):
        super().__init__("Test")
        self.menu = [rumps.MenuItem("A", callback=self.on_a)]
        self.menu["A"].title = "B"
    @rumps.clicked("A")
    def on_a(self, _):
        print("Clicked!")
app = App()
# simulate click
app.menu["A"].callback(None)
