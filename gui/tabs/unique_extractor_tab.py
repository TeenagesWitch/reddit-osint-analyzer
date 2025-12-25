"""Subreddit Analysis Tab."""

import os
import json
import datetime
import collections
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pytz


class SubredditAnalysisTab(ttk.Frame):
    """Tab for analyzing subreddits with comprehensive dashboard."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.subreddit_counts = collections.defaultdict(int)
        self.usernames = set()
        self.user_contributions = collections.defaultdict(int)  # {username: count}
        self.activity_by_date = collections.defaultdict(int)
        self.activity_by_hour_day = collections.defaultdict(lambda: collections.defaultdict(int))
        self.raw_timestamps = []
        self.selected_timezone = pytz.UTC
        self.total_posts = 0
        self.date_range = None
        self._build_ui()

    def _build_ui(self):
        # Top section: File selection and Stats side by side
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', pady=(0, 10))
        
        # Left side: File inputs
        input_frame = ttk.Frame(top_frame)
        input_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Label(input_frame, text='JSONL File A (Posts):').grid(row=0, column=0, sticky='w', padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.file1_path, width=50).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(input_frame, text='Browse...', command=lambda: self._browse(self.file1_path)).grid(row=0, column=2)

        ttk.Label(input_frame, text='JSONL File B (Comments):').grid(row=1, column=0, sticky='w', padx=(0, 5), pady=(5, 0))
        ttk.Entry(input_frame, textvariable=self.file2_path, width=50).grid(row=1, column=1, padx=(0, 5), pady=(5, 0))
        ttk.Button(input_frame, text='Browse...', command=lambda: self._browse(self.file2_path)).grid(row=1, column=2, pady=(5, 0))

        ttk.Button(input_frame, text='Analyze', command=self._analyze).grid(row=2, column=0, pady=10)

        # Right side: Stats panel
        stats_frame = ttk.LabelFrame(top_frame, text='Exploratory Stats', padding=5)
        stats_frame.pack(side='right', fill='both', expand=False)
        self._build_stats_view(stats_frame)

        # Dashboard layout - main container
        dashboard_frame = ttk.Frame(self)
        dashboard_frame.pack(fill='both', expand=True)

        # Left column - Lists
        left_frame = ttk.Frame(dashboard_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        # Unique usernames panel
        username_frame = ttk.LabelFrame(left_frame, text='Unique Usernames', padding=5)
        username_frame.pack(fill='both', expand=True, pady=(0, 5))
        self._build_username_view(username_frame)

        # Top contributors panel
        contributors_frame = ttk.LabelFrame(left_frame, text='Top 20 Contributors', padding=5)
        contributors_frame.pack(fill='both', expand=True)
        self._build_contributors_view(contributors_frame)

        # Right column - Visualizations
        right_frame = ttk.Frame(dashboard_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Activity Tracker
        activity_frame = ttk.LabelFrame(right_frame, text='Activity Tracker', padding=5)
        activity_frame.pack(fill='both', expand=True, pady=(0, 5))
        self.activity_year_var = tk.StringVar(value='All')
        self._build_activity_tracker_view(activity_frame)

        # Day by Day Posting Hours Heatmap
        hour_frame = ttk.LabelFrame(right_frame, text='Day by Day Posting Hours Heatmap', padding=5)
        hour_frame.pack(fill='both', expand=True, pady=(5, 0))
        self._build_hour_heatmap_view(hour_frame)

    def _build_stats_view(self, parent):
        # Use a text widget or multiple labels for better formatting
        self.stats_text = tk.Text(parent, height=8, width=40, wrap='word', font=('Arial', 9), state='disabled')
        self.stats_text.pack(fill='both', expand=True)
        
        # Initial message
        self.stats_text.config(state='normal')
        self.stats_text.insert('1.0', 'Click "Analyze" to see statistics')
        self.stats_text.config(state='disabled')

    def _build_username_view(self, parent):
        # Username list with export
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True)
        
        self.username_tree = ttk.Treeview(list_frame, columns=('Username',), show='headings', height=8)
        self.username_tree.heading('Username', text='Username', command=lambda: self._sort_username_tree())
        self.username_tree.column('Username', anchor='w')
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.username_tree.yview)
        self.username_tree.configure(yscrollcommand=scrollbar.set)
        
        self.username_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        ttk.Button(parent, text='Export Usernames as TXT', command=self._export_usernames).pack(pady=5)

    def _build_contributors_view(self, parent):
        # Top contributors list
        self.contributors_tree = ttk.Treeview(parent, columns=('Username', 'Posts/Comments'), show='headings', height=8)
        self.contributors_tree.heading('Username', text='Username')
        self.contributors_tree.heading('Posts/Comments', text='Posts/Comments', command=lambda: self._sort_contributors_tree('Posts/Comments', False))
        self.contributors_tree.column('Username', anchor='w', width=200)
        self.contributors_tree.column('Posts/Comments', anchor='center', width=120)
        
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=self.contributors_tree.yview)
        self.contributors_tree.configure(yscrollcommand=scrollbar.set)
        
        self.contributors_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _build_activity_tracker_view(self, parent):
        # Year filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(filter_frame, text='Filter by Year:').pack(side='left', padx=(0, 5))
        self.activity_year_dropdown = ttk.Combobox(filter_frame, values=['All'], textvariable=self.activity_year_var, 
                                                   state='readonly', width=12)
        self.activity_year_dropdown.pack(side='left', padx=(0, 5))
        self.activity_year_var.trace('w', lambda *args: self._update_activity_tracker())
        
        # Canvas for activity grid
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill='both', expand=True)
        
        self.activity_canvas = tk.Canvas(canvas_frame, bg='white', height=175)
        scrollbar_activity_h = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.activity_canvas.xview)
        scrollbar_activity_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.activity_canvas.yview)
        self.activity_canvas.configure(xscrollcommand=scrollbar_activity_h.set, yscrollcommand=scrollbar_activity_v.set)
        
        self.activity_canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar_activity_v.grid(row=0, column=1, sticky='ns')
        scrollbar_activity_h.grid(row=1, column=0, sticky='ew')
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

    def _build_hour_heatmap_view(self, parent):
        # Timezone selection
        tz_frame = ttk.Frame(parent)
        tz_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(tz_frame, text='Timezone:').pack(side='left', padx=(0, 5))
        
        timezones = [
            ('UTC', 'UTC'),
            ('US Eastern', 'America/New_York'),
            ('US Central', 'America/Chicago'),
            ('US Mountain', 'America/Denver'),
            ('US Pacific', 'America/Los_Angeles'),
            ('UK', 'Europe/London'),
            ('Central Europe', 'Europe/Berlin'),
            ('Japan', 'Asia/Tokyo'),
            ('Australia Eastern', 'Australia/Sydney'),
        ]
        
        self.timezone_var = tk.StringVar(value='UTC')
        self.timezone_dropdown = ttk.Combobox(tz_frame, values=[tz[0] for tz in timezones], 
                                               textvariable=self.timezone_var, state='readonly', width=20)
        self.timezone_dropdown.pack(side='left', padx=(0, 5))
        self.timezone_map = {tz[0]: tz[1] for tz in timezones}
        self.timezone_var.trace('w', lambda *args: self._on_timezone_changed())
        
        # Canvas for hour heatmap
        self.hour_canvas = tk.Canvas(parent, bg='white', height=250)
        self.hour_canvas.pack(fill='both', expand=True)

    def _browse(self, var):
        path = filedialog.askopenfilename(filetypes=[('JSONL files', '*.jsonl')])
        if path:
            var.set(path)

    def _parse_timestamp(self, ts):
        """Parse timestamp from various formats."""
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            try:
                return datetime.datetime.fromtimestamp(ts)
            except Exception:
                return None
        if isinstance(ts, str):
            try:
                return datetime.datetime.fromisoformat(ts.rstrip('Z'))
            except Exception:
                return None
        return None

    def _validate_jsonl_structure(self, filepath, expected_type):
        """Validate that JSONL file has the expected structure.
        
        Args:
            filepath: Path to JSONL file
            expected_type: 'post' or 'comment'
        
        Returns:
            (is_valid, error_message, subreddit_name) tuple
        """
        if not os.path.isfile(filepath):
            return False, f'File not found: {filepath}', None
        
        try:
            sample_count = 0
            subreddit_name = None
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    
                    sample_count += 1
                    
                    # Extract subreddit name
                    subreddit = obj.get('subreddit')
                    if not subreddit:
                        subreddit_prefixed = obj.get('subreddit_name_prefixed', '')
                        if subreddit_prefixed.startswith('r/'):
                            subreddit = subreddit_prefixed[2:]
                        else:
                            subreddit = subreddit_prefixed
                    
                    if subreddit:
                        if subreddit_name is None:
                            subreddit_name = subreddit
                        elif subreddit_name.lower() != subreddit.lower():
                            return False, f'File is not a valid subreddit JSONL file', None
                    
                    if sample_count > 10:  # Check first 10 valid lines
                        break
                    
                    # Check required fields
                    if not obj.get('subreddit') and not obj.get('subreddit_name_prefixed'):
                        return False, f'Missing subreddit field in {filepath}', None
                    
                    if not obj.get('author'):
                        # Author can be missing for deleted posts, but should exist in structure
                        pass
                    
                    if not obj.get('created_utc') and not obj.get('created'):
                        return False, f'Missing timestamp field in {filepath}', None
                    
                    # Check type-specific fields
                    if expected_type == 'post':
                        # Posts should have 'title' or 'selftext' or 'is_self'
                        if 'title' not in obj and 'is_self' not in obj:
                            return False, f'File {filepath} does not appear to be a posts file (missing post-specific fields)', None
                    
                    elif expected_type == 'comment':
                        # Comments should have 'body' and 'link_id'
                        if 'body' not in obj or 'link_id' not in obj:
                            return False, f'File {filepath} does not appear to be a comments file (missing comment-specific fields)', None
            
            if sample_count == 0:
                return False, f'No valid JSON lines found in {filepath}', None
            
            if subreddit_name is None:
                return False, f'Could not determine subreddit from {filepath}', None
            
            return True, None, subreddit_name
        except Exception as e:
            return False, f'Error reading {filepath}: {e}', None

    def _load_jsonl_files(self):
        """Load and parse JSONL files with structure validation."""
        self.subreddit_counts = collections.defaultdict(int)
        self.usernames = set()
        self.user_contributions = collections.defaultdict(int)
        self.activity_by_date = collections.defaultdict(int)
        self.activity_by_hour_day = collections.defaultdict(lambda: collections.defaultdict(int))
        self.raw_timestamps = []
        self.total_posts = 0
        dates_list = []
        
        file1 = self.file1_path.get()
        file2 = self.file2_path.get()
        
        if not file1 or not file2:
            return False
        
        # Validate file structures and extract subreddits
        subreddit1 = None
        subreddit2 = None
        
        if file1:
            is_valid, error_msg, subreddit = self._validate_jsonl_structure(file1, 'post')
            if not is_valid:
                messagebox.showerror('Validation Error', f'File A (Posts) validation failed:\n{error_msg}')
                return False
            subreddit1 = subreddit
        
        if file2:
            is_valid, error_msg, subreddit = self._validate_jsonl_structure(file2, 'comment')
            if not is_valid:
                messagebox.showerror('Validation Error', f'File B (Comments) validation failed:\n{error_msg}')
                return False
            subreddit2 = subreddit
        
        # Validate that both files are from the same subreddit
        if file1 and file2 and subreddit1 and subreddit2:
            if subreddit1.lower() != subreddit2.lower():
                messagebox.showerror('Validation Error', 
                    f'Subreddit mismatch:\n'
                    f'File A (Posts) is from: r/{subreddit1}\n'
                    f'File B (Comments) is from: r/{subreddit2}\n\n'
                    f'Both files must be from the same subreddit.')
                return False
        
        # Process files
        files_to_process = []
        if file1:
            files_to_process.append((file1, 'post'))
        if file2:
            files_to_process.append((file2, 'comment'))
        
        for filepath, file_type in files_to_process:
            if not os.path.isfile(filepath):
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        self.total_posts += 1
                        
                        # Extract subreddit
                        subreddit = obj.get('subreddit')
                        if not subreddit:
                            subreddit_prefixed = obj.get('subreddit_name_prefixed', '')
                            if subreddit_prefixed.startswith('r/'):
                                subreddit = subreddit_prefixed[2:]
                            else:
                                subreddit = subreddit_prefixed
                        if subreddit:
                            self.subreddit_counts[subreddit] += 1
                        
                        # Extract username
                        author = obj.get('author')
                        if author and author.lower() not in ('[deleted]', 'automoderator'):
                            self.usernames.add(author)
                            self.user_contributions[author] += 1
                        
                        # Extract timestamp
                        ts = obj.get('created_utc') or obj.get('created') or obj.get('timestamp')
                        dt = self._parse_timestamp(ts)
                        if dt:
                            # Store raw timestamp (assume UTC if it's a Unix timestamp)
                            if isinstance(ts, (int, float)):
                                dt_utc = datetime.datetime.utcfromtimestamp(ts)
                                dt_utc = pytz.UTC.localize(dt_utc)
                            else:
                                if dt.tzinfo is None:
                                    dt_utc = pytz.UTC.localize(dt)
                                else:
                                    dt_utc = dt.astimezone(pytz.UTC)
                            
                            self.raw_timestamps.append(dt_utc)
                            date_key = dt_utc.date()
                            self.activity_by_date[date_key] += 1
                            dates_list.append(date_key)
            except Exception as e:
                messagebox.showerror('Error', f'Failed to read {filepath}: {e}')
                return False
        
        if dates_list:
            self.date_range = (min(dates_list), max(dates_list))
        
        return True

    def _analyze(self):
        p1 = self.file1_path.get()
        p2 = self.file2_path.get()
        
        if not p1 or not p2:
            messagebox.showerror('Error', 'Both JSONL files are required.\nFile A (Posts) and File B (Comments) must be provided.')
            return
        
        if not self._load_jsonl_files():
            messagebox.showerror('Error', 'Failed to read JSONL files.')
            return
        
        # Update all views
        self._update_stats()
        self._update_username_view()
        self._update_contributors_view()
        self._populate_year_dropdown()
        self._update_activity_tracker()
        self._update_hour_heatmap()
        
        messagebox.showinfo('Analysis Complete', f'Analyzed {self.total_posts} posts/comments successfully.')

    def _update_stats(self):
        """Calculate and display exploratory statistics."""
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', tk.END)
        
        if self.total_posts == 0:
            self.stats_text.insert('1.0', 'No data available')
            self.stats_text.config(state='disabled')
            return
        
        # Format stats with line breaks
        stats_lines = []
        
        # Basic stats
        if self.subreddit_counts:
            sub_name = next(iter(self.subreddit_counts))
            stats_lines.append(f'Subreddit:\n{sub_name}\n')
        stats_lines.append(f'Total Posts/Comments:\n{self.total_posts:,}\n')
        stats_lines.append(f'Unique Usernames:\n{len(self.usernames):,}\n')
        stats_lines.append(f'Unique Subreddits:\n{len(self.subreddit_counts):,}\n')
        
        # Posts per day (PPD)
        if self.date_range:
            days_span = (self.date_range[1] - self.date_range[0]).days + 1
            ppd = self.total_posts / days_span if days_span > 0 else 0
            stats_lines.append(f'Posts per Day (PPD):\n{ppd:.2f}\n')
            stats_lines.append(f'Date Range:\n{self.date_range[0]} to {self.date_range[1]}\n')
        
        # Posts per hour (PPH)
        if self.date_range:
            days_span = (self.date_range[1] - self.date_range[0]).days + 1
            hours_span = days_span * 24 if days_span > 0 else 1
            pph = self.total_posts / hours_span if hours_span > 0 else 0
            stats_lines.append(f'Posts per Hour (PPH):\n{pph:.2f}\n')
        
        # Average posts per user
        if len(self.usernames) > 0:
            avg_per_user = self.total_posts / len(self.usernames)
            stats_lines.append(f'Avg Posts per User:\n{avg_per_user:.2f}\n')
                
        self.stats_text.insert('1.0', '\n'.join(stats_lines))
        self.stats_text.config(state='disabled')

    def _update_username_view(self):
        """Update unique usernames list."""
        for row in self.username_tree.get_children():
            self.username_tree.delete(row)
        
        sorted_users = sorted(self.usernames)
        for u in sorted_users:
            self.username_tree.insert('', 'end', values=(u,))

    def _update_contributors_view(self):
        """Update top 20 contributors list."""
        for row in self.contributors_tree.get_children():
            self.contributors_tree.delete(row)
        
        # Sort by contribution count (descending) and take top 20
        sorted_contributors = sorted(self.user_contributions.items(), key=lambda x: x[1], reverse=True)[:20]
        
        for username, count in sorted_contributors:
            self.contributors_tree.insert('', 'end', values=(username, count))

    def _update_activity_tracker(self):
        """Update activity tracker (GitHub-style calendar)."""
        self.activity_canvas.delete('all')
        
        if not self.activity_by_date:
            self.activity_canvas.create_text(400, 100, text='No activity data available', fill='gray')
            return

        # Filter by year if selected
        selected_year = self.activity_year_var.get()
        filtered_dates = {}
        if selected_year == 'All':
            filtered_dates = self.activity_by_date
        else:
            try:
                year = int(selected_year)
                filtered_dates = {date: count for date, count in self.activity_by_date.items() if date.year == year}
            except (ValueError, TypeError):
                filtered_dates = self.activity_by_date

        if not filtered_dates:
            self.activity_canvas.create_text(400, 100, text=f'No activity data for year {selected_year}', fill='gray')
            return

        # Determine the year to display
        if selected_year == 'All':
            all_years = sorted(set(date.year for date in self.activity_by_date.keys()))
            if not all_years:
                return
            display_year = all_years[-1]
        else:
            try:
                display_year = int(selected_year)
            except (ValueError, TypeError):
                return

        # Generate all days for the selected year
        year_start = datetime.date(display_year, 1, 1)
        year_end = datetime.date(display_year, 12, 31)
        is_leap = (display_year % 4 == 0 and display_year % 100 != 0) or (display_year % 400 == 0)
        days_in_year = 366 if is_leap else 365
        
        dates_list = []
        current_date = year_start
        while current_date <= year_end:
            dates_list.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        year_filtered = {date: count for date, count in filtered_dates.items() if date.year == display_year}
        max_activity = max(year_filtered.values()) if year_filtered else 1
        
        # Draw grid
        square_size = 12
        spacing = 2
        start_x = 50
        start_y = 30
        days_per_row = 7
        row_height = square_size + spacing
        col_width = square_size + spacing

        # Draw day labels
        day_labels = ['Mon', '', 'Wed', '', 'Fri', '', 'Sun']
        for day_idx in range(7):
            if day_labels[day_idx]:
                self.activity_canvas.create_text(start_x - 25, start_y + day_idx * row_height + square_size // 2, 
                                                text=day_labels[day_idx], anchor='e', font=('Arial', 8))

        # Track months for labels
        current_month = None
        month_start_col = 0
        
        # Draw all squares
        for day_idx, date in enumerate(dates_list):
            row = day_idx % days_per_row
            col = day_idx // days_per_row
            
            if current_month is None or date.month != current_month:
                if current_month is not None:
                    month_cols = col - month_start_col
                    x_pos = start_x + month_start_col * col_width + (month_cols * col_width) // 2
                    month_label = datetime.date(display_year, current_month, 1).strftime('%b')
                    self.activity_canvas.create_text(x_pos, start_y - 15, text=month_label, anchor='n', font=('Arial', 8))
                current_month = date.month
                month_start_col = col
            
            activity = year_filtered.get(date, 0)
            
            # Color intensity
            if activity == 0:
                color = '#ebedf0'
            elif activity < max_activity * 0.25:
                color = '#c6e48b'
            elif activity < max_activity * 0.5:
                color = '#7bc96f'
            elif activity < max_activity * 0.75:
                color = '#239a3b'
            else:
                color = '#196127'

            x = start_x + col * col_width
            y = start_y + row * row_height
            
            rect_id = self.activity_canvas.create_rectangle(
                x, y, x + square_size, y + square_size,
                fill=color, outline='#ffffff', width=1
            )
            
            if activity > 0:
                def make_callback(d, a):
                    return lambda e: self._show_date_info(d, a)
                self.activity_canvas.tag_bind(rect_id, '<Button-1>', make_callback(date, activity))
        
        # Draw last month label
        if current_month is not None:
            month_cols = (len(dates_list) // days_per_row) - month_start_col
            x_pos = start_x + month_start_col * col_width + (month_cols * col_width) // 2
            month_label = datetime.date(display_year, current_month, 1).strftime('%b')
            self.activity_canvas.create_text(x_pos, start_y - 15, text=month_label, anchor='n', font=('Arial', 8))

        # Update scroll region
        num_cols = (days_in_year + days_per_row - 1) // days_per_row
        total_width = num_cols * col_width + start_x + 20
        total_height = 7 * row_height + start_y + 20
        self.activity_canvas.configure(scrollregion=(0, 0, total_width, total_height))

        # Add legend
        legend_y = start_y + 7 * row_height + 10
        self.activity_canvas.create_text(start_x, legend_y, text='Less', anchor='w', font=('Arial', 8))
        colors = ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
        labels = ['No activity', 'Low', 'Medium', 'High', 'Very High']
        for i, (color, label) in enumerate(zip(colors, labels)):
            x = start_x + 100 + i * 80
            self.activity_canvas.create_rectangle(x, legend_y - 5, x + 12, legend_y + 7, fill=color, outline='white')
            self.activity_canvas.create_text(x + 18, legend_y + 1, text=label, anchor='w', font=('Arial', 7))

    def _on_timezone_changed(self):
        """Handle timezone change."""
        tz_name = self.timezone_var.get()
        if tz_name in self.timezone_map:
            try:
                self.selected_timezone = pytz.timezone(self.timezone_map[tz_name])
                self._update_hour_heatmap()
            except Exception:
                pass

    def _update_hour_heatmap(self):
        """Update hour heatmap."""
        self.hour_canvas.delete('all')
        
        if not self.raw_timestamps:
            self.hour_canvas.create_text(400, 125, text='No activity data available', fill='gray')
            return

        # Recalculate hour/day data with current timezone
        hour_day_data = collections.defaultdict(lambda: collections.defaultdict(int))
        for dt_utc in self.raw_timestamps:
            dt_local = dt_utc.astimezone(self.selected_timezone)
            hour = dt_local.hour
            day_of_week = dt_local.weekday()
            hour_day_data[day_of_week][hour] += 1

        max_count = 0
        for day_data in hour_day_data.values():
            if day_data:
                max_count = max(max_count, max(day_data.values()))
        
        if max_count == 0:
            self.hour_canvas.create_text(400, 125, text='No activity data available', fill='gray')
            return

        # Draw heatmap
        cell_size = 18
        spacing = 2
        start_x = 60
        start_y = 30
        num_hours = 24
        num_days = 7
        
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for day_idx in range(num_days):
            y_pos = start_y + day_idx * (cell_size + spacing) + cell_size // 2
            self.hour_canvas.create_text(start_x - 5, y_pos, text=day_labels[day_idx], anchor='e', font=('Arial', 9))

        for hour in range(num_hours):
            if hour % 2 == 0:
                x_pos = start_x + hour * (cell_size + spacing) + cell_size // 2
                self.hour_canvas.create_text(x_pos, start_y - 15, text=str(hour), anchor='n', font=('Arial', 8))

        for day_idx in range(num_days):
            day_data = hour_day_data.get(day_idx, {})
            for hour in range(num_hours):
                count = day_data.get(hour, 0)
                intensity = count / max_count if max_count > 0 else 0
                
                if intensity == 0:
                    color = '#ebedf0'
                elif intensity < 0.25:
                    color = '#c6e48b'
                elif intensity < 0.5:
                    color = '#7bc96f'
                elif intensity < 0.75:
                    color = '#239a3b'
                else:
                    color = '#196127'

                x = start_x + hour * (cell_size + spacing)
                y = start_y + day_idx * (cell_size + spacing)

                rect_id = self.hour_canvas.create_rectangle(
                    x, y, x + cell_size, y + cell_size,
                    fill=color, outline='#ffffff', width=1
                )

                if count > 0:
                    def make_callback(d, h, c):
                        return lambda e: self._show_hour_day_info(d, h, c)
                    self.hour_canvas.tag_bind(rect_id, '<Button-1>', make_callback(day_labels[day_idx], hour, count))

        # Add legend
        legend_y = start_y + num_days * (cell_size + spacing) + 15
        self.hour_canvas.create_text(start_x, legend_y, text='Less', anchor='w', font=('Arial', 8))
        colors = ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
        labels = ['No activity', 'Low', 'Medium', 'High', 'Very High']
        for i, (color, label) in enumerate(zip(colors, labels)):
            x = start_x + 50 + i * 70
            self.hour_canvas.create_rectangle(x, legend_y - 5, x + 12, legend_y + 7, fill=color, outline='white')
            self.hour_canvas.create_text(x + 18, legend_y + 1, text=label, anchor='w', font=('Arial', 7))
        
        self.hour_canvas.create_text(start_x + (num_hours * (cell_size + spacing)) // 2, legend_y + 20, 
                                    text='Hour of Day (0-23)', anchor='n', font=('Arial', 9))

    def _populate_year_dropdown(self):
        """Populate year dropdown."""
        if not self.activity_by_date:
            return
        years = sorted(set(date.year for date in self.activity_by_date.keys()), reverse=True)
        dropdown_values = ['All'] + [str(y) for y in years]
        self.activity_year_dropdown.config(values=dropdown_values)
        if years:
            self.activity_year_var.set(str(years[0]))

    def _show_date_info(self, date, activity):
        """Show date and activity info."""
        messagebox.showinfo('Activity Info', f'Date: {date.strftime("%Y-%m-%d")}\nActivity: {activity} posts/comments')

    def _show_hour_day_info(self, day_name, hour, count):
        """Show hour and day info."""
        messagebox.showinfo('Activity Info', f'Day: {day_name}\nHour: {hour:02d}:00\nActivity: {count} posts/comments')

    def _sort_username_tree(self):
        data = [(self.username_tree.set(k, 'Username'), k) for k in self.username_tree.get_children('')]
        data.sort()
        for index, (_, k) in enumerate(data):
            self.username_tree.move(k, '', index)

    def _sort_contributors_tree(self, col, reverse):
        data = [(self.contributors_tree.set(k, col), k) for k in self.contributors_tree.get_children('')]
        if col == 'Posts/Comments':
            data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=reverse)
        else:
            data.sort(key=lambda x: x[0].lower(), reverse=reverse)
        for index, (_, k) in enumerate(data):
            self.contributors_tree.move(k, '', index)
        self.contributors_tree.heading(col, command=lambda: self._sort_contributors_tree(col, not reverse))

    def _export_usernames(self):
        """Export usernames to TXT file."""
        if not self.username_tree.get_children():
            messagebox.showerror('Error', 'No data to export.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text files', '*.txt')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for r in self.username_tree.get_children():
                    f.write(self.username_tree.set(r, 'Username') + '\n')
            messagebox.showinfo('Exported', f'Exported {len(self.username_tree.get_children())} usernames to {path}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to export: {e}')
