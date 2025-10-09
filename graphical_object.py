class GraphicalObject:
    def __init__(self, kind, params, color=(0, 0, 0)):
        self.kind = kind
        self.params = params
        self.color = color
        self.selected = False

    def to_dict(self):
        return {"kind": self.kind, "params": self.params, "color": self.color}

    @staticmethod
    def from_dict(d):
        return GraphicalObject(d['kind'], d['params'], tuple(d.get('color', (0, 0, 0))))