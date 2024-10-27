import wx
import wx.lib.agw.customtreectrl as CT
import wx.html

class CustomHtmlListBox(wx.html.HtmlListBox):
    def __init__(self, parent, items, tree_ctrl, tree_item, id=wx.ID_ANY, size=(150, 60)):
        super(CustomHtmlListBox, self).__init__(parent, id, size=size)
        self.items = items
        self.tree_ctrl = tree_ctrl  # Reference to the tree control
        self.tree_item = tree_item  # Reference to the corresponding tree item
        self.history_items = []
        self.SetItemCount(0)  # Initial item count
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_single_click)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        # Remove the border by setting a simple style
        self.SetWindowStyleFlag(wx.BORDER_NONE)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
        self.single_click_delayed = None

    def on_focus(self, event):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.Refresh()
        event.Skip()

    def on_focus_lost(self, event):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.Refresh()
        event.Skip()

    def on_single_click(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()        
        # Highlight the corresponding tree item on single click
        print("Single click in HtmlListBox")
        self.tree_ctrl.SelectItem(self.tree_item)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #event.Skip()
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, self.tree_item, event)        
    def ProcessSingleClick(self, item, event):
        if item:
            # self.SelectItem(item)
            print("Single click detected on item in tree")
        self.single_click_delayed = None
    def on_double_click(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None        
        # Highlight the corresponding tree item on double click
        print("Double click in HtmlListBox")
        self.tree_ctrl.SelectItem(self.tree_item)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #
        #event.Skip()

        

    def OnGetItem(self, index):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        return f"<div style='padding: 10px; background-color: #ffffff;'>{self.history_items[index]}</div>"

    def add_history_item(self, text):
        """Add a new history item with multiline text to the HtmlListBox."""
        html_text = text.replace("\n", "<br>")
        formatted_text = f"""
            <b>History Item {len(self.history_items) + 1}</b><br>
            <span style="color: #2d2d2d; font-size: 14px; font-family: Arial, sans-serif;">
                {html_text}
            </span>
        """
        self.history_items.append(formatted_text)
        self.SetItemCount(len(self.history_items))
        self.Refresh()

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
        self.set_custom_expand_collapse_icons()
    def set_custom_expand_collapse_icons(self):
        # Create a larger "+" and "-" bitmap for expand/collapse
        expand_bmp = wx.Bitmap(20, 20)
        collapse_bmp = wx.Bitmap(20, 20)

        # Draw a "+" icon for expand
        dc = wx.MemoryDC(expand_bmp)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(10, 5, 10, 15)
        dc.DrawLine(5, 10, 15, 10)
        dc.SelectObject(wx.NullBitmap)

        # Draw a "-" icon for collapse
        dc = wx.MemoryDC(collapse_bmp)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(5, 10, 15, 10)
        dc.SelectObject(wx.NullBitmap)

        # Create an image list and add custom bitmaps
        image_list = wx.ImageList(20, 20)
        image_list.Add(expand_bmp)   # The first image is the expand icon
        image_list.Add(expand_bmp) # The second image is the collapse icon
        image_list.Add(collapse_bmp) # The second image is the collapse icon
        image_list.Add(collapse_bmp)
        # Assign the image list to the tree control
        self.SetButtonsImageList(image_list)

    def AppendMultilineItem(self, parent, html_items, data=None):
        # Append an item with an empty string as the text
        item = self.AppendItem(parent, "")
        if data is not None:
            self.SetItemData(item, data)

        # Create an instance of CustomHtmlListBox with specific items, passing tree control and item references
        html_list_box = CustomHtmlListBox(self, html_items, self, item, size=(150, 60))
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
            print("Single click detected on item in tree")
        self.single_click_delayed = None

    def OnDoubleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if item:
            self.SelectItem(item)
            print("Double-clicked on item in tree")
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
