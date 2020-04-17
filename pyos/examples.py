import uuid

import mincepy


class Contact(mincepy.SimpleSavable):
    ATTRS = ('name', 'age', 'tel', 'address')
    TYPE_ID = uuid.UUID('e03a4ca8-ef8f-430a-891c-d58da6f7ad3d')

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.ags = None
        self.tel = None
        self.address = None
        self.friends = mincepy.RefList()
