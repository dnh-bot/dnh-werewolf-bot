class Character:
    def __init__(self, player):
	self.player = player
        self.status = None # Could be alive, dead, protected,...


    def on_phase(self, phase):
	if phase == 'day':
            self.on_day()
	elif phase == 'night':
	    self.on_night()
	elif phase == 'role':
	    self.on_role()
