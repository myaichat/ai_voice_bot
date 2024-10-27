import wx
import wx.lib.agw.customtreectrl as CT

class MultilineTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        # Create the base style with required flags
        agwStyle = (CT.TR_HAS_VARIABLE_ROW_HEIGHT |  # Required for multiline
                   CT.TR_HAS_BUTTONS |               # Show expand/collapse buttons
                   CT.TR_NO_LINES |                  # No connection lines
                   CT.TR_FULL_ROW_HIGHLIGHT)         # Highlight full row on selection
        
        # Initialize with explicit agwStyle
        super(MultilineTreeCtrl, self).__init__(parent, id, pos, size, 
                                               agwStyle=agwStyle,
                                               style=wx.WANTS_CHARS)
    
    def AppendMultilineItem(self, parent, text, data=None):
        # Ensure we pass ct_type=1 for multiline text
        item = self.AppendItem(parent, text, ct_type=1)
        
        if data is not None:
            self.SetItemData(item, data)
            
        return item

class ExampleFrame(wx.Frame):
    def __init__(self):
        super(ExampleFrame, self).__init__(None, title="Multiline Tree Control Example", 
                                         size=(400, 500))
        
        # Create panel to hold the tree
        panel = wx.Panel(self)
        
        # Create the tree control with explicit size
        self.tree = MultilineTreeCtrl(panel, size=(380, 480))
        
        # Create a sizer for the panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        
        # Add root and example items
        root = self.tree.AddRoot("Root")
        
        # Add multiline items
        parent1 = self.tree.AppendMultilineItem(root, "Parent Item 1\nWith multiple lines\nof text")
        child1 = self.tree.AppendMultilineItem(parent1, "This is a child item\nwith two lines")
        child2 = self.tree.AppendMultilineItem(parent1, "Another child\nwith even more\nlines of text\nto display")
        
        parent2 = self.tree.AppendMultilineItem(root, "Parent Item 2\nAlso multiline")
        
        # Expand all items
        self.tree.ExpandAll()
        
        # Layout the frame
        self.Layout()
        
        # Bind size event to handle resizing
        self.Bind(wx.EVT_SIZE, self.OnSize)
    
    def OnSize(self, event):
        self.Layout()
        event.Skip()

if __name__ == '__main__':
    app = wx.App(False)
    frame = ExampleFrame()
    frame.Show()
    app.MainLoop()