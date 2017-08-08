# Format: [("<example_name>","<file_name>"),("<example_name>","<file_name>"),...]
_example_list = [
    ("Blikaj", "blink.txt"),
    ("PWM - LEDka s nastaviteľnou intenzitou", "pwm.txt")]

def get_example_list(self):
    """Returns a list of example names (only their 'user' names, not actual file names)"""
    return [x[0] for x in _example_list]

def get_file_by_id(self, id):
    """Returns the content (plain text) of selected example (by id of _example_list)"""
    return res.get_file_content(_example_list[id][1])