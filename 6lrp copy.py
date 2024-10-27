import wx

class MultilineTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TR_DEFAULT_STYLE):
        super().__init__(parent, id, pos, size, style)
        
        # Bind custom paint event
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Store item heights
        self.item_heights = {}
    
    def GetItemLevel(self, item):
        """Calculate the level of an item (depth in the tree)"""
        level = 0
        parent = self.GetItemParent(item)
        while parent.IsOk():
            level += 1
            parent = self.GetItemParent(parent)
        return level
        
    def AppendMultilineItem(self, parent, text, data=None):
        # Create the item
        item = self.AppendItem(parent, "")
        
        # Calculate required height based on text wrapping
        dc = wx.ClientDC(self)
        
        # Get the available width (tree width minus some padding for indent)
        tree_width = self.GetSize().width
        indent_level = self.GetItemLevel(item)
        available_width = max(100, tree_width - (indent_level * 20) - 40)  # Minimum width of 100
        
        # Wrap text and calculate height
        # Using GetTextExtent for a simpler height calculation
        line_height = dc.GetTextExtent("Tg")[1]  # Height of a typical line
        num_lines = len(text.split('\n'))
        height = line_height * num_lines + 4  # Add a little padding
        
        # Store the height and text for this item
        self.item_heights[item] = (height, text)
        
        # Set the item's label to the first line for default display
        first_line = text.split('\n')[0]
        self.SetItemText(item, first_line)
        
        # Set item data if provided
        if data is not None:
            self.SetItemData(item, data)
        
        return item
    
    def OnPaint(self, evt):
        # Let the default paint handler run first
        evt.Skip()
        
        # Then draw our custom multiline text
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        
        # Iterate through visible items
        item = self.GetFirstVisibleItem()
        while item.IsOk():
            if item in self.item_heights:
                height, text = self.item_heights[item]
                
                # Get item rectangle
                rect = self.GetBoundingRect(item)
                
                # Calculate available width for text
                indent_level = self.GetItemLevel(item)
                available_width = max(100, self.GetSize().width - (indent_level * 20) - 40)
                
                # Adjust rectangle for text placement
                text_rect = wx.Rect(rect.x + 20, rect.y, available_width, height)
                if 0:
                    # Draw the multiline text
                    #dc.SetClippingRect(rect)
                    
                    y = text_rect.y + 2  # Starting y position with small padding
                    for line in text.split('\n'):
                        dc.DrawText(line, text_rect.x, y)
                        y += dc.GetTextExtent(line)[1]
                    
                    dc.DestroyClippingRegion()
            
            item = self.GetNextVisible(item)

class ExampleFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Multiline Tree Control Example", size=(400, 500))
        
        self.tree = MultilineTreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_HAS_BUTTONS)
        
        # Add some example items
        root = self.tree.AddRoot("Root")
        
        # Add items with multiline text
        parent1 = self.tree.AppendMultilineItem(root, "Parent Item 1\nWith multiple lines\nof text")
        child1 = self.tree.AppendMultilineItem(parent1, "This is a child item\nwith two lines")
        child2 = self.tree.AppendMultilineItem(parent1, "Another child\nwith even more\nlines of text\nto display")
        
        parent2 = self.tree.AppendMultilineItem(root, "Parent Item 2\nAlso multiline")
        
        # Expand all items
        self.tree.ExpandAll()

if __name__ == '__main__':
    app = wx.App()
    frame = ExampleFrame()
    frame.Show()
    app.MainLoop()