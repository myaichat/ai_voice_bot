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
        
        # Bind single-click and double-click events to the tree control
        self.Bind(wx.EVT_LEFT_DOWN, self.OnSingleClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        
        # Initialize a variable for the delayed single-click call
        self.single_click_delayed = None

    def AppendMultilineItem(self, parent, text, data=None):
        # Append item without checkbox
        item = self.AppendItem(parent, text)
        
        # Create a button and attach it to the tree item as a window
        button = wx.Button(self, label="Button")
        self.SetItemWindow(item, button)
        
        # Bind single-click button event and embed the item text directly
        button.Bind(wx.EVT_BUTTON, lambda event: self.OnButtonClicked(event, text))
        
        if data is not None:
            self.SetItemData(item, data)
            
        return item
    
    def OnButtonClicked(self, event, item_text):
        # Display the message with the embedded item text
        wx.MessageBox(f"Button clicked on item '{item_text}'")

    def OnSingleClick(self, event):
        # Cancel any pending single-click
        if self.single_click_delayed:
            self.single_click_delayed.Stop()

        # Set a delayed call for single-click, allowing for a double-click check
        self.single_click_delayed = wx.CallLater(200, self.ProcessSingleClick, event)

    def ProcessSingleClick(self, event):
        # Get the item at the position of the single click
        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        
        if item:
            # Ensure the item is highlighted (selected)
            self.SelectItem(item)

            # Retrieve the button (or any window) associated with the item
            window = self.GetItemWindow(item)
            
            # Check if the window is a button or simply log the item text
            item_text = self.GetItemText(item)
            if isinstance(window, wx.Button):
                wx.MessageBox(f"Single click detected on button of item '{item_text}'")
            else:
                wx.MessageBox(f"Single click detected on item '{item_text}' without button")
        
        # Clear the delayed call reference
        self.single_click_delayed = None

    def OnDoubleClick(self, event):
        # Cancel the single-click action if double-click detected
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None
        
        # Get the item at the position of the double-click
        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        
        if item:
            # Ensure the item is highlighted (selected)
            self.SelectItem(item)

            # Retrieve the button (or any window) associated with the item
            window = self.GetItemWindow(item)
            
            # Check if the window is a button
            if isinstance(window, wx.Button):
                item_text = self.GetItemText(item)
                wx.MessageBox(f"Button double-clicked on item '{item_text}'")
        
        # Skip the event to allow other handlers to process it
        event.Skip()

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
