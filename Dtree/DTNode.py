class DTNode:

    def __init__(self, v):
        self.parent = None
        self.children = set()
        self.val = v
        self.nte = set()
        self.size = 1