import wx
import wx.lib.agw.customtreectrl as CT
import wx.html

class CustomHtmlListBox(wx.html.HtmlListBox):
    def __init__(self, parent, items, id=wx.ID_ANY, size=(150, 60)):
        super(CustomHtmlListBox, self).__init__(parent, id, size=size)
        self.items = items
        self.history_items = []
        self.SetItemCount(0)  # Initial item count  
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_single_click)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        # Remove the border by setting a simple style
        self.SetWindowStyleFlag(wx.BORDER_NONE)   
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost) 
    def on_focus(self, event):
        print("Focus gained")
        """Handle focus gain to ensure background color remains white."""
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.Refresh()
        event.Skip()

    def on_focus_lost(self, event):
        print("Focus lost")
        """Handle focus loss to ensure background color remains white."""
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.Refresh()
        event.Skip()                    
    def on_single_click(self, event):   
        print("Single click")
        # Get the position of the mouse click
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        pass
    def OnGetItem(self, index):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        return f"<div style='padding: 10px; background-color: #ffffff;'>{self.history_items[index]}</div>"

    def add_history_item(self, text):
        """Add a new history item with multiline text to the HtmlListBox."""
        # Format the text to use <br> for line breaks
        html_text = text.replace("\n", "<br>")
        
        # Optional: Customize appearance with HTML and CSS
        formatted_text = f"""
            <b>History Item {len(self.history_items) + 1}</b><br>
            <span style="color: #2d2d2d; font-size: 14px; font-family: Arial, sans-serif;">
                {html_text}
            </span>
        """
        
        # Add formatted text to the list and update the control
        self.history_items.append(formatted_text)
        self.SetItemCount(len(self.history_items))
        self.Refresh()

    def on_double_click(self, event):
        """Handle double-click on a list item."""
        # Get the position of the mouse click
        x, y = event.GetPosition()
        
        # Determine the item index at the clicked position
        item_index = self.HitTest(wx.Point(x, y))
        
        if item_index != wx.NOT_FOUND:
            # Fetch the item content (for demonstration)
            item_content = self.history_items[item_index]
            wx.MessageBox(f"{item_index}: You double-clicked on:\n\n{item_content}", "Item Double-Clicked")
        else:
            # No item found at this position
            wx.MessageBox("No item found at the clicked position.", "Info")
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

class MultilineTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        agwStyle = (CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                    CT.TR_HAS_BUTTONS |
                    CT.TR_NO_LINES |
                    CT.TR_FULL_ROW_HIGHLIGHT)
        super(MultilineTreeCtrl, self).__init__(parent, id, pos, size, 
                                                agwStyle=agwStyle,
                                                style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnSingleClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.single_click_delayed = None

    def AppendMultilineItem(self, parent, html_items, data=None):
        # Append an item with an empty string as the text
        item = self.AppendItem(parent, "")
        if data is not None:
            self.SetItemData(item, data)

        # Create an instance of CustomHtmlListBox with specific items
        html_list_box = CustomHtmlListBox(self, html_items, size=(150, 60))
        self.SetItemWindow(item, html_list_box)
        
        # Add sample history items to the HtmlListBox
        html_list_box.add_history_item("First line\nSecond line\nThird line")
        return item
    
    def OnSingleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if flags & CT.TREE_HITTEST_ONITEMBUTTON:
            event.Skip()
            return

        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, item, event)

    def ProcessSingleClick(self, item, event):
        if item:
            self.SelectItem(item)
            print("Single click detected on item")
        self.single_click_delayed = None

    def OnDoubleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if item:
            self.SelectItem(item)
            print("Double-clicked on item")
        event.Skip()

class ExampleFrame(wx.Frame):
    def __init__(self):
        super(ExampleFrame, self).__init__(None, title="Multiline Tree Control Example", 
                                           size=(400, 500))
        panel = wx.Panel(self)
        self.tree = MultilineTreeCtrl(panel, size=(380, 480))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        
        root = self.tree.AddRoot("Root")
        
        # Add parent and child items with unique HTML content for each HtmlListBox
        parent1 = self.tree.AppendMultilineItem(root,
                                                ["<b>Parent Info 1</b>", "<i>Additional Info</i>"])
        child1 = self.tree.AppendMultilineItem(parent1,
                                               ["<b>Child Info 1</b>", "<i>Extra Info</i>"])
        child2 = self.tree.AppendMultilineItem(parent1,
                                               ["<b>Child Info 2</b>", "<i>Extra Details</i>"])
        self.tree.ExpandAll()
        
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.OnSize)
    
    def OnSize(self, event):
        self.Layout()
        event.Skip()

if __name__ == '__main__':
    app = wx.App(False)
    frame = ExampleFrame()
    frame.Show()
    app.MainLoop()
