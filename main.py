#author Ryan Bailey

from os.path import isfile, dirname, realpath
import gi, json, datetime, math
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango, GLib

class Window(Gtk.Window):
    def __init__(self):
        super().__init__(title="Prilog V1 by Ryan Bailey")
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.handle_key_pressed)
        WIDTH, HEIGHT = 600, 400
        self.set_size_request(WIDTH, HEIGHT)
        self.set_resizable(resizable=False)

        self.new_post_layout = Gtk.Grid()
        self.view_posts_swindow = Gtk.ScrolledWindow()
        self.view_posts_swindow.set_policy(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.view_posts_layout = Gtk.Grid()
        self.select_date_range_window = SelectDateRangeWindow(self)
        self.view_posts_text_view = Gtk.TextView()
        self.view_posts_text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.view_posts_text_view.set_editable(False)
        self.view_posts_swindow.add(self.view_posts_text_view)

        self.new_post_layout.set_column_homogeneous(True) #sets all columns to be the same width
        self.view_posts_layout.set_column_homogeneous(True)

        self.search_tag_entry = Gtk.Entry()
        self.search_content_entry = Gtk.Entry()
        self.search_date_button = Gtk.Button(label="Select Date/Range")
        self.search_tag_label = Gtk.Label(label="Search for Tag:")
        self.search_content_label = Gtk.Label(label="Search Content:")
        self.search_date_label = Gtk.Label(label="No date or date range selected.")

        self.view_posts_button = Gtk.Button(label="View Posts")
        self.new_post_button = Gtk.Button(label="New Post")
        self.publish_button = Gtk.Button(label="Publish Post")
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view_swindow = Gtk.ScrolledWindow()
        self.text_view_swindow.set_policy(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.text_view_swindow.add(self.text_view)

        self.set_tag_label = Gtk.Label(label="Set Tag:")
        self.tag_entry = Gtk.Entry()

        self.view_posts_button.connect("clicked", self.view_posts_button_clicked)
        self.new_post_button.connect("clicked", self.new_post_button_clicked)
        self.publish_button.connect("clicked", self.publish_post)
        self.search_date_button.connect("clicked", self.select_date_range)
        self.text_view.connect("size-allocate", self.text_view_changed)
        self.view_posts_swindow.connect("edge-reached", self.handle_scroll_event)

        self.text_view.set_vexpand(True)
        self.text_view_swindow.set_vexpand(True)
        self.view_posts_button.set_hexpand(True)
        self.publish_button.set_hexpand(True)
        self.view_posts_swindow.set_vexpand(True)
        self.new_post_button.set_hexpand(True)

        self.new_post_layout.attach(self.set_tag_label,             left=0, top=0, width=1, height=1)
        self.new_post_layout.attach(self.tag_entry,                 left=1, top=0, width=3, height=1)
        self.new_post_layout.attach(self.text_view_swindow,         left=0, top=1, width=4, height=1)
        self.new_post_layout.attach(self.view_posts_button,         left=0, top=2, width=2, height=1)
        self.new_post_layout.attach(self.publish_button,            left=2, top=2, width=2, height=1)

        self.view_posts_layout.attach(self.search_tag_label,        left=0, top=0, width=2, height=1)
        self.view_posts_layout.attach(self.search_tag_entry,        left=2, top=0, width=4, height=1)
        self.view_posts_layout.attach(self.search_content_label,    left=0, top=1, width=2, height=1)
        self.view_posts_layout.attach(self.search_content_entry,    left=2, top=1, width=4, height=1)
        self.view_posts_layout.attach(self.search_date_button,      left=0, top=2, width=2, height=1)
        self.view_posts_layout.attach(self.search_date_label,       left=2, top=2, width=4, height=1)
        self.view_posts_layout.attach(self.view_posts_swindow,      left=0, top=3, width=6, height=1)
        self.view_posts_layout.attach(self.new_post_button,         left=0, top=4, width=3, height=1)

        self.date_range = []                    #[[day_1, month_1, year_1], [day_2, month_2, year_2]] (modified by date_range_selected)
        self.dates_selected = [False, False]    #date_1_selected, date_2_selected (modified by date_range_selected)
        self.search_tag_text = ""               #the contents of the search tag entry (updated every keyevent)
        self.search_content_text = ""           #the contents of the search content entry (updated every keyevent)
        self.range_to_load = [0, 20]            #the range of relevant posts (updated by handle_scroll_event)
        
        self.master = Gtk.Box()
        self.master.add(self.new_post_layout)
        self.add(self.master)
        self.set_focus(self.text_view)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
    
    def check_for_postsfile(self):
        #if no posts file found on start up, send a dialog box asking the user if you want to create one if no is selected, exit.
        if not isfile(dirname(realpath(__file__)) + "/.postsfile"):
            dialog = NoPostsFileDialog(self)
            response = dialog.run()
            dialog.destroy()
            if response == Gtk.ResponseType.YES:
                with open(dirname(realpath(__file__)) + "/.postsfile", "w+") as postsfile:
                    postsfile.write(json.dumps([]))
                GLib.idle_add(self.populate_view_posts_text_view)
            else:
                Gtk.main_quit()

    def get_posts_data(self):
        with open(dirname(realpath(__file__)) + "/.postsfile", "rt") as postsfile:
            posts = json.loads(postsfile.read())
            if self.dates_selected[0] and self.dates_selected[1]:
                posts = [x for x in posts if (
                            datetime.date(year=self.date_range[0][2], month=self.date_range[0][1], day=self.date_range[0][0]) <= (
                            datetime.date(year=x["year"], month=x["month"], day=x["day"])) <= (
                            datetime.date(year=self.date_range[1][2], month=self.date_range[1][1], day=self.date_range[1][0])))]
            elif self.dates_selected[0]:
                posts = [x for x in posts if (
                            datetime.date(year=self.date_range[0][2], month=self.date_range[0][1], day=self.date_range[0][0]) == (
                            datetime.date(year=x["year"], month=x["month"], day=x["day"])))]
            elif self.dates_selected[1]:
                posts = [x for x in posts if (
                            datetime.date(year=self.date_range[1][2], month=self.date_range[1][1], day=self.date_range[1][0]) == (
                            datetime.date(year=x["year"], month=x["month"], day=x["day"])))]
            if self.search_content_text != "":
                posts = [x for x in posts if x["text"].lower().find(self.search_content_text.lower()) != -1]
            if self.search_tag_text != "":
                if self.search_tag_text.lower() == "none":
                    posts = [x for x in posts if x["tag"] == ""]
                else:
                    posts = [x for x in posts if x["tag"].lower().find(self.search_tag_text.lower()) != -1]
            return posts[::-1]

    def get_meta_line(self, data, i):
        meta_line = "Date: " + self.fstr(data[i]["day"]) + "/" + self.fstr(data[i]["month"]) + "/" + str(data[i]["year"]) + \
                    "  " + self.fstr(data[i]["hour"]) + ":" + self.fstr(data[i]["minute"])
        meta_line += " "*(40-len(meta_line)) + "Tag: " + data[i]["tag"]
        return meta_line
    
    def add_posts_to_buffer(self, buff, data, range_to_load, top=False):
        mark_pairs = []
        if top:
            for i in range(range_to_load[0], range_to_load[1]):
                meta_line = self.get_meta_line(data, i)
                post_line = data[i]["text"]
                buff.insert(buff.get_start_iter(), "\n" + post_line + "\n\n\n")
                end_mark = buff.create_mark(None, buff.get_start_iter(), left_gravity=False)
                buff.insert(buff.get_start_iter(), meta_line)
                mark_pairs += [[buff.create_mark(None, buff.get_start_iter(), left_gravity=False), end_mark]]
        else:
            for i in range(range_to_load[1] - 1 if len(data) > range_to_load[1] else len(data) - 1, range_to_load[0] - 1, -1):
                meta_line = self.get_meta_line(data, i)
                post_line = data[i]["text"]
                start_mark = buff.create_mark(None, buff.get_end_iter(), left_gravity=True)
                buff.insert(buff.get_end_iter(), meta_line)
                mark_pairs += [[start_mark, buff.create_mark(None, buff.get_end_iter(), left_gravity=True)]]
                buff.insert(buff.get_end_iter(), "\n" + post_line + "\n\n\n")
        return mark_pairs
    
    def remove_posts_from_buffer(self, buff, data, old_range_to_load, top): 
        #figure out which posts are to be removed, how many buffer lines are in these posts (plus how many are added when inserted)
        #and then remove these lines from the buffer
        num_of_buffer_lines_to_remove = 0
        if top:
            range_to_remove = [self.range_to_load[0], old_range_to_load[0]]
            for i in range(range_to_remove[1], range_to_remove[0]):
                num_of_buffer_lines_to_remove += (4 + data[i]["text"].count("\n"))
            end_iter = buff.get_end_iter()
            #if char_offset too large, iter at end of line given
            start_iter = buff.get_iter_at_line_offset(buff.get_line_count() - num_of_buffer_lines_to_remove - 1, char_offset=0)
        else: #bottom
            range_to_remove = [old_range_to_load[1] - 1, self.range_to_load[1] - 1]
            for i in range(range_to_remove[1], range_to_remove[0]):
                num_of_buffer_lines_to_remove += (4 + data[i]["text"].count("\n"))
            start_iter = buff.get_start_iter()
            #calculate char_offset
            lines = buff.get_text(buff.get_start_iter(), buff.get_end_iter(), include_hidden_chars=False).split("\n")
            char_offset = len(lines[num_of_buffer_lines_to_remove - 1])
            end_iter = buff.get_iter_at_line_offset(num_of_buffer_lines_to_remove, char_offset=char_offset)
        buff.delete(start_iter, end_iter)
        GLib.idle_add(self.view_posts_text_view.queue_draw)
    
    #populate self.posts with post textviews and add them to view_posts_swindow
    def populate_view_posts_text_view(self, old_range_to_load=None, top=True):
        #remove data from the view posts textview
        buff = self.view_posts_text_view.get_buffer()
        tag = buff.create_tag(weight=Pango.Weight.BOLD)
        #add data to the view_posts textview
        data = self.get_posts_data()
        mark_pairs = [] #stores the text marks representing the start and end of locations to be made bold
        if not old_range_to_load: #if this isn't called by self.handle_scroll_event
            buff.set_text("")
            mark_pairs += self.add_posts_to_buffer(buff, data, self.range_to_load)
            self.set_vptv_to_bottom()
        else: #called by self.handle_scroll_event
            #get the mark of the top-left buffer coord, update the buffer and then scroll to that mark
            #add the posts to the top if the top edge reached, and add them to the bottom if the bottom edge reached
            #don't delete the buffer or the mark that indicates where to scroll will lose its meaning
            #the scrolling isn't instantaneous, which sucks, but I'm happy to have got it working for now
            if top: #load older posts (top edge reached)
                iter_ = buff.get_start_iter()
                mark = buff.create_mark(None, iter_, left_gravity=False)
                #insert the new section to load at the start of the buffer, then scroll to mark
                mark_pairs += self.add_posts_to_buffer(buff, data, [old_range_to_load[1], self.range_to_load[1]], top=top)
                self.remove_posts_from_buffer(buff, data, old_range_to_load, top)
            else: #load newer posts (bottom edge reached)
                self.set_vptv_to_bottom()
                buffer_x, buffer_y = self.view_posts_text_view.get_visible_rect().x, self.view_posts_text_view.get_visible_rect().y
                iter_ = self.view_posts_text_view.get_iter_at_location(buffer_x, buffer_y)
                mark = buff.create_mark(None, iter_, left_gravity=True)
                #insert the new section to load at the end of the buffer, then scroll to mark
                mark_pairs += self.add_posts_to_buffer(buff, data, [self.range_to_load[0], old_range_to_load[0]], top=top)
                self.remove_posts_from_buffer(buff, data, old_range_to_load, top)
            GLib.idle_add(self.view_posts_text_view.scroll_to_mark, mark, 0, True, 0, 0)

        for mark_pair in mark_pairs:
            buff.apply_tag(tag, buff.get_iter_at_mark(mark_pair[0]), buff.get_iter_at_mark(mark_pair[1]))

    def publish_post(self, button):
        buff = self.text_view.get_buffer()
        post_text = buff.get_text(buff.get_start_iter(), buff.get_end_iter(), include_hidden_chars=False)
        if post_text == "":
            return
        posts = self.get_posts_data()
        now = datetime.datetime.now()
        new_post = {"text":post_text, "hour":now.time().hour, "minute":now.time().minute, "second":now.time().second,
                    "year":now.date().year, "month":now.date().month, "day":now.date().day, "tag":self.tag_entry.get_text()}
        if new_post["tag"].lower() == "none":
            new_post["tag"] = ""
        posts = [new_post] + posts
        posts = posts[::-1]
        with open(dirname(realpath(__file__)) + "/.postsfile", "wt") as postsfile:
            postsfile.seek(0)
            postsfile.truncate()
            postsfile.write(json.dumps(posts, sort_keys=True, indent=2))
        buff.set_text("")
        #hacky way to get the vptv to update so get_vptv_height() works
        self.view_posts_button_clicked(None)
        self.new_post_button_clicked(None)
    
    def view_posts_button_clicked(self, button):
        self.master.remove(self.new_post_layout)
        self.master.add(self.view_posts_layout)
        GLib.idle_add(self.populate_view_posts_text_view)
        self.show_all()

    def new_post_button_clicked(self, button):
        self.master.remove(self.view_posts_layout)
        self.master.add(self.new_post_layout)
        self.set_focus(self.text_view)
        self.show_all()

    def text_view_changed(self, widget, event, data=None):
        adj = self.text_view_swindow.get_vadjustment()
        adj.set_value(math.inf)
    
    def set_vptv_to_bottom(self):
        buff = self.view_posts_text_view.get_buffer()
        adj = self.view_posts_swindow.get_vadjustment()
        adj.set_value(math.inf)
        
    def handle_key_pressed(self, widget, event):
        if Gdk.keyval_name(event.keyval) == "Escape" and self.has_toplevel_focus():
            self.iconify()
            return True
        elif self.get_focus() == self.text_view:
            if Gdk.keyval_name(event.keyval) == "Return" and (event.state & Gdk.ModifierType.CONTROL_MASK): #ctrl-enter pressed
                self.publish_post(None)
                return True #cancels the key event so that the "\n" is not inserted into the buffer atfer it is cleared by publish_post()
            elif Gdk.keyval_name(event.keyval) == "Tab":
                self.tag_entry.grab_focus()
                return True
        elif self.get_focus() == self.tag_entry and Gdk.keyval_name(event.keyval) == "Tab":
            self.set_focus(self.text_view)
            return True
        elif self.get_focus() == self.search_tag_entry:
            GLib.idle_add(self.update_search_tag_text)
        elif self.get_focus() == self.search_content_entry:
            Glib.idle_add(self.update_search_content_text)
        GLib.idle_add(self.view_posts_text_view.queue_draw)
    
    def update_search_content_text(self):
        self.search_content_text = self.search_content_entry.get_buffer().get_text()
        self.populate_view_posts_text_view()
    
    def update_search_tag_text(self):
        self.search_tag_text = self.search_tag_entry.get_buffer().get_text()
        self.populate_view_posts_text_view()
    
    def select_date_range(self, button):
        self.select_date_range_window.show_all()
    
    #take in an int and return it as a string to padded with zeros - i.e. 2 --> "02" 
    def fstr(self, i):
        return str(i) if i >= 10 else "0" + str(i)

    #called by SelectDateRangeWindow when it's confirm button is hit
    def date_range_selected(self, date_1_selected, date_2_selected, day_1, day_2, month_1, month_2, year_1, year_2):
        self.dates_selected = [date_1_selected, date_2_selected]
        if date_1_selected and date_2_selected:
            date_1 = datetime.date(year=year_1, month=month_1, day=day_1)
            date_2 = datetime.date(year=year_2, month=month_2, day=day_2)
            if date_2 < date_1:
                day_1, month_1, year_1, day_2, month_2, year_2 = day_2, month_2, year_2, day_1, month_1, year_1
            elif date_2 == date_1:
                date_2_selected = False
                day_2, month_2, year_2 = [None]*3
        self.date_range = [[day_1, month_1, year_1], [day_2, month_2, year_2]]
        if date_1_selected and date_2_selected:
            self.search_date_label.set_text("Selected: " + self.fstr(day_1) + "/" + self.fstr(month_1) + "/" + str(year_1) + " to " + \
                                            self.fstr(day_2) + "/" + self.fstr(month_2) + "/" + str(year_2))
        elif date_1_selected or date_2_selected:
            if date_1_selected:
                self.search_date_label.set_text("Selected: " + self.fstr(day_1) + "/" + self.fstr(month_1) + "/" + str(year_1))
            else: #date_2_selected
                self.search_date_label.set_text("Selected: " + self.fstr(day_2) + "/" + self.fstr(month_2) + "/" + str(year_2))            
        else: #neither calendar has a selected date
            self.search_date_label.set_text("No date or date range selected.")
        self.populate_view_posts_text_view()

    def handle_scroll_event(self, scrolled_window, pos):
        posts = self.get_posts_data()
        max_num_of_posts_to_change = 5
        #change the viewable posts without a noticable screen change by updating the text view then scrolling down intantaneously
        if scrolled_window == self.view_posts_swindow:
            #check if there are new posts to load
            if pos == Gtk.PositionType.TOP:
                if self.range_to_load[1] < len(posts):
                    num_of_posts_to_change = max_num_of_posts_to_change if (
                        len(posts) - self.range_to_load[1] >= max_num_of_posts_to_change) else len(posts) - self.range_to_load[1]
                    old_range_to_load = self.range_to_load
                    self.range_to_load = [x + num_of_posts_to_change for x in self.range_to_load]
                    self.populate_view_posts_text_view(old_range_to_load=old_range_to_load, top=True)
                    return True
            else: #pos == Gtk.PositionType.BOTTOM
                if self.range_to_load[0] > 0:
                    num_of_posts_to_change = max_num_of_posts_to_change if(
                        self.range_to_load[0] >= max_num_of_posts_to_change) else self.range_to_load[0]
                    old_range_to_load = self.range_to_load
                    self.range_to_load = [x - num_of_posts_to_change for x in self.range_to_load]
                    self.populate_view_posts_text_view(old_range_to_load=old_range_to_load, top=False)
                    return True

class NoPostsFileDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="No Posts File found", transient_for=parent)
        self.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES)
        label = Gtk.Label(label="No Posts File found.\nDo you want to create a new one?\nIf no, the program will exit.")
        box = self.get_content_area()
        box.add(label)
        self.set_resizable(resizable=False)
        self.show_all()

class SelectDateRangeWindow(Gtk.Window):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(title="Date Selector")
        self.set_resizable(False)
        self.date_selector_1 = Gtk.Calendar()
        self.date_selector_2 = Gtk.Calendar()
        self.date_selected_label_1 = Gtk.Label(label="No Date Selected")
        self.date_selected_label_2 = Gtk.Label(label="No Date Selected")
        self.deselect_button_1 = Gtk.Button(label="Deselect")
        self.deselect_button_2 = Gtk.Button(label="Deselect")
        self.cancel_button = Gtk.Button(label="Cancel")
        self.confirm_button = Gtk.Button(label="Confirm")

        self.deselect_button_1.set_sensitive(False)
        self.deselect_button_2.set_sensitive(False)

        self.date_selector_1.connect("day-selected", self.day_selected)
        self.date_selector_2.connect("day-selected", self.day_selected)
        self.deselect_button_1.connect("clicked", self.deselect_button_clicked)
        self.deselect_button_2.connect("clicked", self.deselect_button_clicked)
        self.cancel_button.connect("clicked", self.cancel_button_clicked)
        self.confirm_button.connect("clicked", self.confirm_button_clicked)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.attach(self.date_selector_1,          left=0, top=0, width=2, height=1)
        self.grid.attach(self.date_selector_2,          left=2, top=0, width=2, height=1)
        self.grid.attach(self.date_selected_label_1,    left=0, top=1, width=1, height=1)
        self.grid.attach(self.date_selected_label_2,    left=2, top=1, width=1, height=1)
        self.grid.attach(self.deselect_button_1,        left=1, top=1, width=1, height=1)
        self.grid.attach(self.deselect_button_2,        left=3, top=1, width=1, height=1)
        self.grid.attach(self.cancel_button,            left=0, top=2, width=2, height=1)
        self.grid.attach(self.confirm_button,           left=2, top=2, width=2, height=1)

        self.add(self.grid)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.date_1_selected, self.date_2_selected = [False]*2
        self.day_1, self.day_2, self.month_1, self.month_2, self.year_1, self.year_2 = [None]*6
    
    def day_selected(self, calendar):
        if calendar == self.date_selector_1:
            self.date_1_selected = True
            self.year_1, self.month_1, self.day_1 = calendar.get_date()
            self.month_1 += 1 #months are returned as between 0-11, change to 1-12
            self.date_selected_label_1.set_text(str(self.day_1) + "/" + str(self.month_1) + "/" + str(self.year_1))
            self.deselect_button_1.set_sensitive(True)
        else: #calendar == self.date_selector_2
            self.date_2_selected = True
            self.year_2, self.month_2, self.day_2 = calendar.get_date()
            self.month_2 += 1 #months are returned as between 0-11, change to 1-12
            self.date_selected_label_2.set_text(str(self.day_2) + "/" + str(self.month_2) + "/" + str(self.year_2))
            self.deselect_button_2.set_sensitive(True)
    
    def deselect_button_clicked(self, button):
        if button == self.deselect_button_1:
            self.date_1_selected = False
            self.date_selected_label_1.set_text("No Date Selected")
            self.day_1, self.month_1, self.year_1 = [None]*3
        else: #button = self.deselect_button_2
            self.date_2_selected = False
            self.date_selected_label_2.set_text("No Date Selected")
            self.day_2, self.month_2, self.year_2 = [None]*3
        button.set_sensitive(False)
    
    def cancel_button_clicked(self, button):
        self.deselect_button_clicked(self.deselect_button_1)
        self.deselect_button_clicked(self.deselect_button_2)
        self.set_visible(False)

    def confirm_button_clicked(self, button):
        self.set_visible(False)
        self.parent.date_range_selected(self.date_1_selected, self.date_2_selected, self.day_1, self.day_2, 
                                        self.month_1, self.month_2, self.year_1, self.year_2)

if __name__ == "__main__":
    win = Window()
    GLib.idle_add(win.check_for_postsfile)
    if isfile(dirname(realpath(__file__)) + "/.postsfile"):
        GLib.idle_add(win.populate_view_posts_text_view)
    Gtk.main()