import os
import random
from datetime import date

from gi.repository import Gio
from gi.repository import Gtk

from GTG.core.logger import log
from gettext import gettext as _

class Gamify:
    PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
    PLUGIN_NAMESPACE = 'gamify'
    DEFAULT_ANALITICS = {
        "last_task_date": date.today(), # The date of the last task marked as done
        "last_task_number": 0, # The number of tasks done today
        "streak": 0, # The number of days in which the goal was achieved
        "goal_achieved": False, # achieved today's goal
        "score": 0
    }
    DEFAULT_PREFERENCES = {
        "goal": 3,
        "ui_type": "FULL"
    }
    LEVELS = {
        100: 'Beginner',
        1000: 'Novice',
        2000: 'prefessional',
        4000: 'Expert',
        9000: 'Master',
        13000: 'Master II',
        19000: 'Grand Master',
        25000: 'Productivity Lord'
    }

    def __init__(self):
        self.configureable = True

        self.builder = Gtk.Builder()
        path = f"{self.PLUGIN_PATH}/prefs.ui"
        self.builder.add_from_file(path)

        self.menu = None
        self.stack = None
        self.submenu = None

        self.data = None
        self.preferences = None

    def _init_dialog_pref(self):
        # Get the dialog widget
        self.pref_dialog = self.builder.get_object('gamify-pref-dialog')
        # Get the buttonSpin
        self.spinner = self.builder.get_object('target-spin-button')
        # Get the radio buttons
        self.button1 = self.builder.get_object('radiobutton0')
        self.button2 = self.builder.get_object('radiobutton1')
        self.button3 = self.builder.get_object('radiobutton2')


        if self.pref_dialog is None or self.spinner is None:
            raise ValueError('Cannot load preference dialog widget')

        SIGNALS = {
            "on_preferences_changed": self.on_preferences_changed,
            "on_dialog_close": self.on_preferences_closed
        }
        self.builder.connect_signals(SIGNALS)

    def add_headerbar_button(self):
        self.headerbar_button = self.builder.get_object('gamify-headerbar')

        self.headerbar = self.plugin_api.get_header()
        self.headerbar.add(self.headerbar_button)

    def remove_headerbar_button(self):
        self.headerbar.remove(self.headerbar_button)

    def add_levelbar(self):
        self.quickadd_pane = self.plugin_api.get_quickadd_pane()
        self.levelbar = self.builder.get_object('goal-levelbar')
        self.quickadd_pane.set_orientation(Gtk.Orientation.VERTICAL)
        self.quickadd_pane.add(self.levelbar)

    def remove_levelbar(self):
        self.quickadd_pane.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.quickadd_pane.remove(self.levelbar)

    def activate(self, plugin_api):
        self.plugin_api = plugin_api
        self.browser = plugin_api.get_browser()

        # Load preferences and data
        self.analytics_load()
        self.preferences_load()

        # Settings up the menu 
        self.add_ui()

        # Init the preference dialog
        try:
            self._init_dialog_pref()
        except ValueError:
            self.configureable = False
            log.debug('Cannot load preference dialog widget')

        # Connect to the signals
        self.connect_id = self.browser.connect("task-marked-as-done", self.on_marked_as_done)

        self.update_date()
        self.update_streak()
        self.analytics_save()
        self.update_widget()

    def on_marked_as_done(self, sender, task_id):
        log.debug('a task has been marked as done')
        self.analytics_load()
        self.preferences_load()

        # Update the date, if it is different from today
        self.update_date()

        # Increase the number of tasks done and update the streak
        # if the goal number of tasks was achieved
        self.data['last_task_number'] += 1
        self.update_streak()
        self.data['score'] += self.get_points_for_task(task_id)
        self.analytics_save()
        self.update_widget()

    def get_points_for_task(self, task_id):
        """Returns the number of point for doing a perticular task

        If a task is taged as @hard: the user receives 3 points
        If a task is taged as @meduim: the use receives 2 points
        If a task is taged as @easy: the user receives 1 point
        """
        easy = False
        meduim = False
        hard = False
        task = self.plugin_api.get_requester().get_task(task_id)
        tags = task.get_tags_name()
        for tag in tags:
            if tag == '@easy':
                easy = True
            elif tag == '@meduim':
                meduim = True
            elif tag == '@hard':
                hard = True

        if easy:
            return 1
        if meduim:
            return 2
        if hard:
            return 3
        return 1

    def OnTaskOpened(self, plugin_api):
        pass

    def is_full(self):
        """Return True if ui type is FULL"""
        return self.preferences['ui_type'] == 'FULL'

    def has_button(self):
        """Return True if UI contains a BUTTON"""
        return self.preferences['ui_type'] in ('BUTTON', 'FULL')

    def has_levelbar(self):
        """Return True if UI contains a LEVELBAR"""
        return self.preferences['ui_type'] in ('LEVELBAR', 'FULL')

    def add_ui(self):
        """Add the appropriate UI elements"""
        if self.preferences['ui_type'] == 'FULL':
            self.add_headerbar_button()
            self.add_levelbar()
        elif self.preferences['ui_type'] == 'BUTTON':
            self.add_headerbar_button()
        else:
            self.add_levelbar()

    def remove_ui(self):
        """Remove all the UI elements of the plugin"""
        try:
            self.remove_headerbar_button()
        except AttributeError:
            pass
        try:
            self.remove_levelbar()
        except AttributeError:
            pass

    def deactivate(self, plugin_api):
        self.remove_ui()

    def is_configurable(self):
        return True

    def preferences_load(self):
        self.preferences = self.plugin_api.load_configuration_object(
            self.PLUGIN_NAMESPACE, "preferences",
            default_values=self.DEFAULT_PREFERENCES
        )

    def save_preferences(self):
        self.plugin_api.save_configuration_object(
            self.PLUGIN_NAMESPACE,
            "preferences",
            self.preferences
        )

    def analytics_load(self):
        self.data = self.plugin_api.load_configuration_object(
            self.PLUGIN_NAMESPACE, "analytics",
            default_values=self.DEFAULT_ANALITICS
        )

    def analytics_save(self):
        self.plugin_api.save_configuration_object(
            self.PLUGIN_NAMESPACE,
            "analytics",
            self.data
        )

    def update_streak(self):
        if self.data['last_task_number'] >= self.preferences['goal']:
            if not self.data['goal_achieved']:
                self.data['goal_achieved'] = True
                self.data['streak'] += 1

    def update_date(self):
        today = date.today()
        if self.data['last_task_date'] != today:
            if self.data['last_task_number'] < self.preferences['goal']:
                self.data['streak'] = 0
            self.data['goal_achieved'] = False
            self.data['last_task_number'] = 0
            self.data['last_task_date'] = today

    def get_current_level(self):
        return min([(score, level) for score,level in self.LEVELS.items() if score >= self.get_score()])[1]

    def get_score(self):
        return self.data['score']

    def get_number_of_tasks(self):
        return self.data['last_task_number']

    def get_streak(self):
        return self.data['streak']

    def button_update_score(self):
        """Update the score in the BUTTON widget"""
        score_label = self.builder.get_object('score_label')
        score_label.set_markup(_("<b>{current_level}</b>").format(current_level=self.get_current_level()))
        score_value = self.builder.get_object('score_value')
        score_value.set_markup(_('You have: <b>{score}</b> points').format(score=self.get_score()))

    def button_update_goal(self):
        """Update the numbers of tasks done in the BUTTON widget"""
        headerbar_label_button = self.builder.get_object('headerbar-label-button')
        headerbar_label = self.builder.get_object('headerbar-label')
        headerbar_msg = self.builder.get_object('headerbar-msg')

        tasks_done = self.get_number_of_tasks()
        goal = self.preferences['goal']
        headerbar_label_button.set_markup("{tasks_done}/{goal}".format(tasks_done=tasks_done, goal=goal))

        # Select a msg and emojo depending on the number of tasks done.
        if tasks_done >= goal:
            emoji = ["\U0001F60E", "\U0001F920", "\U0001F640"]
            headerbar_label.set_markup(random.choice(emoji))
            headerbar_msg.set_markup(_("Good Job!\nYou have achieved your goal."))
        elif tasks_done >= 1:
            emoji = ["\U0001F600", "\U0001F60C"]
            headerbar_label.set_markup(random.choice(emoji))
            headerbar_msg.set_markup(_("Only a few tasks to go!"))
        else:
            emoji = ["\U0001F643", "\U0001F648"]
            headerbar_label.set_markup(random.choice(emoji))
            headerbar_msg.set_markup(_("Get Down to Business\nYou haven't achieved any tasks today."))

    def button_update_streak(self):
        """Update the streak numbers in the BUTTON widget"""
        streak_number = self.builder.get_object('streak_number')
        streak_emoji = self.builder.get_object('streak_emoji')
        if self.get_streak() > 0:
            streak_emoji.set_markup("\U0001F525")
        else:
            streak_emoji.set_markup("\U0001F9CA")
        streak_number.set_markup(_("You've completed your goal {streak} day in a row.").format(streak=self.get_streak()))

    def update_levelbar(self):
        self.levelbar.set_min_value(0.0)
        self.levelbar.set_max_value(self.preferences['goal'])
        self.levelbar.set_value(self.get_number_of_tasks())


    def update_widget(self):
        """Update the information depending on the UI type"""
        if self.has_button():
            self.button_update_score()
            self.button_update_goal()
            self.button_update_streak()

        if self.has_levelbar():
            self.update_levelbar()

    def update_goal(self):
        if self.has_button():
            self.button_update_goal()
        if self.has_levelbar():
            self.update_levelbar()

    def update_ui(self):
        """Updates the type of ui (FULL, BUTTON, or LEVELBAR)"""
        self.remove_ui()
        self.add_ui()


    def configure_dialog(self, manager_dialog):
        if not self.configureable:
            log.debug('trying to open preference menu, but dialog widget not loaded')
            return

        self.preferences_load()
        self.pref_dialog.set_transient_for(manager_dialog)

        self.spinner.set_value(self.preferences['goal'])
        if self.preferences['ui_type'] == 'FULL':
            self.button1.set_active(True)
        elif self.preferences['ui_type'] == 'BUTTON':
            self.button2.set_active(True)
        else:
            self.button3.set_active(True)

        self.pref_dialog.show_all()

    def on_preferences_closed(self, widget=None, data=None):
        self.pref_dialog.hide()
        return True

    def on_preferences_changed(self, widget=None, data=None):
        self.preferences_load()

        # Get the new preferences
        self.preferences['goal'] = self.spinner.get_value_as_int()
        if self.button1.get_active():
            self.preferences['ui_type'] = "FULL"
        elif self.button2.get_active():
            self.preferences['ui_type'] = "BUTTON"
        else:
            self.preferences['ui_type'] = "LEVELBAR"

        self.save_preferences()
        # Update the type of UI
        self.update_ui()
        # Update the goal in the widget(s)
        self.update_goal()