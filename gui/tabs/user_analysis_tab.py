"""User Analysis Tab."""

import os
import json
import datetime
import collections
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pytz


class UserAnalysisTab(ttk.Frame):
    """Tab for analyzing user activity from JSONL files."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.subreddit_counts = {}
        self.activity_by_date = {}
        self.activity_by_hour_day = collections.defaultdict(lambda: collections.defaultdict(int))  # {day_of_week: {hour: count}}
        self.raw_timestamps = []
        self.total_posts = 0
        self.total_comments = 0
        self.username = None
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

        # Left column - Subreddits (takes 40% width)
        left_frame = ttk.Frame(dashboard_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self._build_subreddit_view(left_frame)

        # Right column - Activity visualizations (takes 60% width)
        right_frame = ttk.Frame(dashboard_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Top right - Activity Tracker
        activity_frame = ttk.LabelFrame(right_frame, text='Activity Tracker', padding=5)
        activity_frame.pack(fill='both', expand=True, pady=(0, 5))
        self.activity_year_var = tk.StringVar(value='All')
        self._build_activity_tracker_view(activity_frame)

        # Bottom right - Day by Day Posting Hours Heatmap
        hour_frame = ttk.LabelFrame(right_frame, text='Day by Day Posting Hours Heatmap', padding=5)
        hour_frame.pack(fill='both', expand=True, pady=(5, 0))
        self._build_hour_heatmap_view(hour_frame)

    def _build_stats_view(self, parent):
        """Build the exploratory stats display."""
        self.stats_text = tk.Text(parent, width=40, height=8, wrap='word', state='disabled', font=('Arial', 9))
        self.stats_text.pack(fill='both', expand=True)

    def _build_subreddit_view(self, parent):
        # Label frame for subreddits
        subreddit_frame = ttk.LabelFrame(parent, text='Subreddits (sorted by frequency)', padding=5)
        subreddit_frame.pack(fill='both', expand=True)
        
        # Treeview for subreddits
        self.subreddit_tree = ttk.Treeview(subreddit_frame, columns=('Subreddit', 'Count'), show='headings')
        self.subreddit_tree.heading('Subreddit', text='Subreddit', command=lambda: self._sort_subreddit_tree('Subreddit', False))
        self.subreddit_tree.heading('Count', text='Count', command=lambda: self._sort_subreddit_tree('Count', False))
        self.subreddit_tree.column('Subreddit', anchor='w', width=200)
        self.subreddit_tree.column('Count', anchor='center', width=80)
        
        scrollbar = ttk.Scrollbar(subreddit_frame, orient='vertical', command=self.subreddit_tree.yview)
        self.subreddit_tree.configure(yscrollcommand=scrollbar.set)
        
        self.subreddit_tree.pack(side='left', fill='both', expand=True)
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
        
        # Canvas for activity grid (horizontal scroll)
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill='both', expand=True)
        
        self.activity_canvas = tk.Canvas(canvas_frame, bg='white', height=175)
        scrollbar_activity_h = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.activity_canvas.xview)
        scrollbar_activity_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.activity_canvas.yview)
        self.activity_canvas.configure(xscrollcommand=scrollbar_activity_h.set, yscrollcommand=scrollbar_activity_v.set)
        
        # Grid layout for canvas and scrollbars
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
        
        # Common timezones
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
        # Initialize timezone to UTC
        self.selected_timezone = pytz.UTC
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
        """Validate that JSONL file has the expected structure and extract author.
        
        Args:
            filepath: Path to JSONL file
            expected_type: 'post' or 'comment'
        
        Returns:
            (is_valid, error_message, author_name) tuple
        """
        if not os.path.isfile(filepath):
            return False, f'File not found: {filepath}', None
        
        try:
            sample_count = 0
            author_name = None
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
                    
                    # Extract author name
                    author = obj.get('author')
                    if author and author.lower() not in ('[deleted]', 'automoderator'):
                        if author_name is None:
                            author_name = author
                        elif author_name.lower() != author.lower():
                            return False, f'File is not a valid user JSONL file', None
                    
                    if sample_count > 10:  # Check first 10 valid lines
                        break
                    
                    # Check required fields
                    if not obj.get('author'):
                        # Author can be missing for deleted posts, but should exist in structure
                        pass
                    
                    if not obj.get('created_utc') and not obj.get('created'):
                        return False, f'Missing timestamp field in {filepath}', None
                    
                    # Check for subreddit field (should exist)
                    if not obj.get('subreddit') and not obj.get('subreddit_name_prefixed'):
                        return False, f'Missing subreddit field in {filepath}', None
                    
                    # Check type-specific fields
                    if expected_type == 'post':
                        # Posts should have 'title' or 'is_self'
                        if 'title' not in obj and 'is_self' not in obj:
                            return False, f'File {filepath} does not appear to be a posts file (missing post-specific fields)', None
                    
                    elif expected_type == 'comment':
                        # Comments should have 'body' and 'link_id'
                        if 'body' not in obj or 'link_id' not in obj:
                            return False, f'File {filepath} does not appear to be a comments file (missing comment-specific fields)', None
            
            if sample_count == 0:
                return False, f'No valid JSON lines found in {filepath}', None
            
            if author_name is None:
                return False, f'Could not determine author from {filepath}. File may contain only deleted posts/comments.', None
            
            return True, None, author_name
        except Exception as e:
            return False, f'Error reading {filepath}: {e}', None

    def _load_jsonl_files(self):
        """Load and parse JSONL files with structure validation."""
        self.subreddit_counts = collections.defaultdict(int)
        self.activity_by_date = collections.defaultdict(int)
        self.activity_by_hour_day = collections.defaultdict(lambda: collections.defaultdict(int))
        self.raw_timestamps = []  # Store raw datetime objects for timezone conversion
        self.total_posts = 0
        self.total_comments = 0
        self.username = None
        dates_list = []

        file1 = self.file1_path.get()
        file2 = self.file2_path.get()

        if not file1 or not file2:
            return False

        # Validate file structures and extract authors
        author1 = None
        author2 = None

        if file1:
            is_valid, error_msg, author = self._validate_jsonl_structure(file1, 'post')
            if not is_valid:
                messagebox.showerror('Validation Error', f'File A (Posts) validation failed:\n{error_msg}')
                return False
            author1 = author

        if file2:
            is_valid, error_msg, author = self._validate_jsonl_structure(file2, 'comment')
            if not is_valid:
                messagebox.showerror('Validation Error', f'File B (Comments) validation failed:\n{error_msg}')
                return False
            author2 = author

        # Validate that both files are from the same user
        if file1 and file2 and author1 and author2:
            if author1.lower() != author2.lower():
                messagebox.showerror('Validation Error', 
                    f'User mismatch:\n'
                    f'File A is from user: u/{author1}\n'
                    f'File B is from user: u/{author2}\n\n'
                    f'Both files must be from the same Reddit user.')
                return False
            self.username = author1  # Store username

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

                        # Count posts vs comments
                        if file_type == 'post':
                            self.total_posts += 1
                        elif file_type == 'comment':
                            self.total_comments += 1

                        # Extract subreddit
                        subreddit = obj.get('subreddit')
                        if not subreddit:
                            # Try subreddit_name_prefixed (format: "r/subredditname")
                            subreddit_prefixed = obj.get('subreddit_name_prefixed', '')
                            if subreddit_prefixed.startswith('r/'):
                                subreddit = subreddit_prefixed[2:]  # Remove "r/" prefix
                            else:
                                subreddit = subreddit_prefixed
                        
                        if subreddit:
                            self.subreddit_counts[subreddit] += 1

                        # Extract timestamp (prefer created_utc, fallback to created, then timestamp)
                        ts = obj.get('created_utc') or obj.get('created') or obj.get('timestamp')
                        dt = self._parse_timestamp(ts)
                        if dt:
                            # Store raw timestamp (assume UTC if it's a Unix timestamp)
                            if isinstance(ts, (int, float)):
                                dt_utc = datetime.datetime.utcfromtimestamp(ts)
                                dt_utc = pytz.UTC.localize(dt_utc)
                            else:
                                # If it's already a datetime, assume UTC
                                if dt.tzinfo is None:
                                    dt_utc = pytz.UTC.localize(dt)
                                else:
                                    dt_utc = dt.astimezone(pytz.UTC)
                            
                            self.raw_timestamps.append(dt_utc)
                            
                            # Use UTC for date tracking (date doesn't change with timezone usually)
                            date_key = dt_utc.date()
                            self.activity_by_date[date_key] += 1
                            dates_list.append(date_key)
            except Exception as e:
                messagebox.showerror('Error', f'Failed to read {filepath}: {e}')
                return False

        if dates_list:
            self.date_range = (min(dates_list), max(dates_list))

        return (self.total_posts + self.total_comments) > 0

    def _analyze(self):
        p1 = self.file1_path.get()
        p2 = self.file2_path.get()
        
        if not p1 or not p2:
            messagebox.showerror('Error', 'Both JSONL files are required.\nFile A (Posts) and File B (Comments) must be provided.')
            return

        if not self._load_jsonl_files():
            messagebox.showerror('Error', 'Failed to parse JSONL files or no valid data found.')
            return

        # Update all views
        self._update_stats()
        self._update_subreddit_view()
        
        # Update activity tracker (populate year dropdown first)
        self._populate_year_dropdown()
        self._update_activity_tracker()
        
        # Update hour heatmap view (will use current timezone selection)
        self._update_hour_heatmap()

        total_activity = self.total_posts + self.total_comments
        messagebox.showinfo('Analysis Complete', f'Analyzed {total_activity} posts/comments successfully.')

    def _update_stats(self):
        """Calculate and display exploratory statistics."""
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', tk.END)
        
        total_activity = self.total_posts + self.total_comments
        if total_activity == 0:
            self.stats_text.insert('1.0', 'No data available')
            self.stats_text.config(state='disabled')
            return
        
        # Format stats with line breaks
        stats_lines = []
        
        # Basic stats
        if self.username:
            stats_lines.append(f'Username:\nu/{self.username}\n')
        stats_lines.append(f'Total Posts:\n{self.total_posts:,}\n')
        stats_lines.append(f'Total Comments:\n{self.total_comments:,}\n')
        stats_lines.append(f'Total Activity:\n{total_activity:,}\n')
        stats_lines.append(f'Unique Subreddits:\n{len(self.subreddit_counts):,}\n')
        
        # Posts per day (PPD)
        if self.date_range:
            days_span = (self.date_range[1] - self.date_range[0]).days + 1
            ppd = total_activity / days_span if days_span > 0 else 0
            stats_lines.append(f'Posts per Day (PPD):\n{ppd:.2f}\n')
            stats_lines.append(f'Date Range:\n{self.date_range[0]} to {self.date_range[1]}\n')
        
        # Posts per hour (PPH)
        if self.date_range:
            days_span = (self.date_range[1] - self.date_range[0]).days + 1
            hours_span = days_span * 24 if days_span > 0 else 1
            pph = total_activity / hours_span if hours_span > 0 else 0
            stats_lines.append(f'Posts per Hour (PPH):\n{pph:.2f}\n')
        
        # Average activity per subreddit
        if len(self.subreddit_counts) > 0:
            avg_per_sub = total_activity / len(self.subreddit_counts)
            stats_lines.append(f'Avg Activity per Sub:\n{avg_per_sub:.2f}\n')
        
        # Posts vs Comments ratio
        if self.total_comments > 0:
            post_ratio = (self.total_posts / total_activity) * 100
            comment_ratio = (self.total_comments / total_activity) * 100
            stats_lines.append(f'Posts: {post_ratio:.1f}%\nComments: {comment_ratio:.1f}%\n')
                
        self.stats_text.insert('1.0', '\n'.join(stats_lines))
        self.stats_text.config(state='disabled')

    def _update_subreddit_view(self):
        # Clear existing items
        for item in self.subreddit_tree.get_children():
            self.subreddit_tree.delete(item)

        # Sort by count (descending)
        sorted_subs = sorted(self.subreddit_counts.items(), key=lambda x: x[1], reverse=True)
        
        for subreddit, count in sorted_subs:
            self.subreddit_tree.insert('', 'end', values=(subreddit, count))

    def _update_activity_tracker(self):
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
            # Use the year range from the data
            all_years = sorted(set(date.year for date in self.activity_by_date.keys()))
            if not all_years:
                self.activity_canvas.create_text(400, 100, text='No activity data available', fill='gray')
                return
            display_year = all_years[-1]  # Use most recent year
        else:
            try:
                display_year = int(selected_year)
            except (ValueError, TypeError):
                self.activity_canvas.create_text(400, 100, text='Invalid year selection', fill='gray')
                return

        # Generate all days for the selected year (365 or 366 days)
        year_start = datetime.date(display_year, 1, 1)
        year_end = datetime.date(display_year, 12, 31)
        
        # Check if it's a leap year
        is_leap = (display_year % 4 == 0 and display_year % 100 != 0) or (display_year % 400 == 0)
        days_in_year = 366 if is_leap else 365
        
        # Generate all dates for the year
        dates_list = []
        current_date = year_start
        while current_date <= year_end:
            dates_list.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        # Calculate max activity for color scaling (from filtered data for this year)
        year_filtered = {date: count for date, count in filtered_dates.items() if date.year == display_year}
        max_activity = max(year_filtered.values()) if year_filtered else 1
        
        # Group days into rows (we'll display in a grid, 7 days per row for alignment)
        # But we want to show all 365/366 days, so we'll have 53 rows (53 * 7 = 371, but we only use what we need)
        days_per_row = 7
        num_rows = (days_in_year + days_per_row - 1) // days_per_row  # Ceiling division

        # Draw grid horizontally (days going left to right, wrapped into rows)
        square_size = 12
        spacing = 2
        start_x = 50
        start_y = 30
        days_per_row = 7
        row_height = square_size + spacing
        col_width = square_size + spacing

        # Draw day labels on the left (vertical) - only show Mon, Wed, Fri like GitHub
        day_labels = ['Mon', '', 'Wed', '', 'Fri', '', 'Sun']
        for day_idx in range(7):
            if day_labels[day_idx]:  # Only draw label if not empty
                self.activity_canvas.create_text(start_x - 25, start_y + day_idx * row_height + square_size // 2, 
                                                text=day_labels[day_idx], anchor='e', font=('Arial', 8))

        # Track current month to show month labels at the top
        current_month = None
        month_start_col = 0
        
        # Draw all 365/366 squares in a grid
        for day_idx, date in enumerate(dates_list):
            # Calculate row and column position
            row = day_idx % days_per_row  # Day of week (0=Mon, 6=Sun)
            col = day_idx // days_per_row  # Week number
            
            # Show month label when month changes
            if current_month is None or date.month != current_month:
                if current_month is not None:
                    # Draw month label centered on previous month's columns
                    month_cols = col - month_start_col
                    x_pos = start_x + month_start_col * col_width + (month_cols * col_width) // 2
                    month_label = datetime.date(display_year, current_month, 1).strftime('%b')
                    self.activity_canvas.create_text(x_pos, start_y - 15, text=month_label, anchor='n', font=('Arial', 8))
                current_month = date.month
                month_start_col = col
            
            # Get activity for this date
            activity = year_filtered.get(date, 0)
            
            # Calculate color intensity (0-4 levels) - matching GitHub colors
            if activity == 0:
                color = '#ebedf0'  # Light gray
            elif activity < max_activity * 0.25:
                color = '#c6e48b'  # Light green
            elif activity < max_activity * 0.5:
                color = '#7bc96f'  # Medium green
            elif activity < max_activity * 0.75:
                color = '#239a3b'  # Dark green
            else:
                color = '#196127'  # Darkest green

            # Position: x is based on column (week), y is based on row (day of week)
            x = start_x + col * col_width
            y = start_y + row * row_height
            
            # Draw square
            rect_id = self.activity_canvas.create_rectangle(
                x, y, x + square_size, y + square_size,
                fill=color, outline='#ffffff', width=1
            )

            # Add click binding to show date and activity
            def make_callback(d, a):
                return lambda e: self._show_date_info(d, a)
            self.activity_canvas.tag_bind(rect_id, '<Button-1>', make_callback(date, activity))
        
        # Draw last month label
        if current_month is not None:
            month_cols = (len(dates_list) // days_per_row) - month_start_col
            x_pos = start_x + month_start_col * col_width + (month_cols * col_width) // 2
            month_label = datetime.date(display_year, current_month, 1).strftime('%b')
            self.activity_canvas.create_text(x_pos, start_y - 15, text=month_label, anchor='n', font=('Arial', 8))

        # Update canvas scroll region (horizontal layout)
        num_cols = (days_in_year + days_per_row - 1) // days_per_row  # Number of columns needed
        total_width = num_cols * col_width + start_x + 20
        total_height = 7 * row_height + start_y + 20
        self.activity_canvas.configure(scrollregion=(0, 0, total_width, total_height))

        # Add legend at the bottom
        legend_y = start_y + 7 * (square_size + spacing) + 10
        self.activity_canvas.create_text(start_x, legend_y, text='Less', anchor='w', font=('Arial', 8))
        colors = ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
        labels = ['No activity', 'Low', 'Medium', 'High', 'Very High']
        for i, (color, label) in enumerate(zip(colors, labels)):
            x = start_x + 100 + i * 80
            self.activity_canvas.create_rectangle(x, legend_y - 5, x + 12, legend_y + 7, fill=color, outline='white')
            self.activity_canvas.create_text(x + 18, legend_y + 1, text=label, anchor='w', font=('Arial', 7))

    def _on_timezone_changed(self):
        """Handle timezone change - recalculate heatmap."""
        tz_name = self.timezone_var.get()
        if tz_name in self.timezone_map:
            try:
                self.selected_timezone = pytz.timezone(self.timezone_map[tz_name])
                self._update_hour_heatmap()
            except Exception:
                pass

    def _update_hour_heatmap(self):
        self.hour_canvas.delete('all')
        
        if not self.raw_timestamps:
            self.hour_canvas.create_text(400, 125, text='No activity data available', fill='gray')
            return

        # Recalculate hour/day data with current timezone
        hour_day_data = collections.defaultdict(lambda: collections.defaultdict(int))
        for dt_utc in self.raw_timestamps:
            # Convert to selected timezone
            dt_local = dt_utc.astimezone(self.selected_timezone)
            hour = dt_local.hour
            day_of_week = dt_local.weekday()  # 0=Monday, 6=Sunday
            hour_day_data[day_of_week][hour] += 1

        # Calculate max activity for color scaling
        max_count = 0
        for day_data in hour_day_data.values():
            if day_data:
                max_count = max(max_count, max(day_data.values()))
        
        if max_count == 0:
            self.hour_canvas.create_text(400, 125, text='No activity data available', fill='gray')
            return

        # Heatmap dimensions
        cell_size = 18
        spacing = 2
        start_x = 60
        start_y = 30
        num_hours = 24
        num_days = 7
        
        # Day labels (Monday = 0, Sunday = 6)
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Draw day labels on the left
        for day_idx in range(num_days):
            y_pos = start_y + day_idx * (cell_size + spacing) + cell_size // 2
            self.hour_canvas.create_text(start_x - 5, y_pos, text=day_labels[day_idx], anchor='e', font=('Arial', 9))

        # Draw hour labels at the top
        for hour in range(num_hours):
            if hour % 2 == 0:  # Show every 2 hours
                x_pos = start_x + hour * (cell_size + spacing) + cell_size // 2
                self.hour_canvas.create_text(x_pos, start_y - 15, text=str(hour), anchor='n', font=('Arial', 8))

        # Draw heatmap cells
        for day_idx in range(num_days):  # 0=Monday, 6=Sunday
            day_data = hour_day_data.get(day_idx, {})
            for hour in range(num_hours):
                count = day_data.get(hour, 0)
                
                # Calculate color intensity (0-4 levels)
                intensity = count / max_count if max_count > 0 else 0
                if intensity == 0:
                    color = '#ebedf0'  # Light gray
                elif intensity < 0.25:
                    color = '#c6e48b'  # Light green
                elif intensity < 0.5:
                    color = '#7bc96f'  # Medium green
                elif intensity < 0.75:
                    color = '#239a3b'  # Dark green
                else:
                    color = '#196127'  # Darkest green

                # Calculate position
                x = start_x + hour * (cell_size + spacing)
                y = start_y + day_idx * (cell_size + spacing)

                # Draw cell
                rect_id = self.hour_canvas.create_rectangle(
                    x, y, x + cell_size, y + cell_size,
                    fill=color, outline='#ffffff', width=1
                )

                # Add click binding to show details
                if count > 0:
                    def make_callback(d, h, c):
                        return lambda e: self._show_hour_day_info(d, h, c)
                    self.hour_canvas.tag_bind(rect_id, '<Button-1>', make_callback(day_labels[day_idx], hour, count))

        # Add legend at the bottom
        legend_y = start_y + num_days * (cell_size + spacing) + 15
        self.hour_canvas.create_text(start_x, legend_y, text='Less', anchor='w', font=('Arial', 8))
        colors = ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
        labels = ['No activity', 'Low', 'Medium', 'High', 'Very High']
        for i, (color, label) in enumerate(zip(colors, labels)):
            x = start_x + 50 + i * 70
            self.hour_canvas.create_rectangle(x, legend_y - 5, x + 12, legend_y + 7, fill=color, outline='white')
            self.hour_canvas.create_text(x + 18, legend_y + 1, text=label, anchor='w', font=('Arial', 7))
        
        # X-axis label
        self.hour_canvas.create_text(start_x + (num_hours * (cell_size + spacing)) // 2, legend_y + 20, 
                                    text='Hour of Day (0-23)', anchor='n', font=('Arial', 9))

    def _populate_year_dropdown(self):
        """Populate the year dropdown with available years from activity data."""
        if not self.activity_by_date:
            return
        
        years = sorted(set(date.year for date in self.activity_by_date.keys()), reverse=True)
        dropdown_values = ['All'] + [str(y) for y in years]
        self.activity_year_dropdown.config(values=dropdown_values)
        if years:
            self.activity_year_var.set(str(years[0]))  # Default to most recent year

    def _show_date_info(self, date, activity):
        """Show date and activity information when clicking on a square."""
        messagebox.showinfo('Activity Info', f'Date: {date.strftime("%Y-%m-%d")}\nActivity: {activity} posts/comments')

    def _show_hour_day_info(self, day_name, hour, count):
        """Show hour and day information when clicking on a heatmap cell."""
        messagebox.showinfo('Activity Info', f'Day: {day_name}\nHour: {hour:02d}:00\nActivity: {count} posts/comments')

    def _sort_subreddit_tree(self, col, reverse):
        data = [(self.subreddit_tree.set(k, col), k) for k in self.subreddit_tree.get_children('')]
        if col == 'Count':
            data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=reverse)
        else:
            data.sort(key=lambda x: x[0].lower(), reverse=reverse)
        for index, (_, k) in enumerate(data):
            self.subreddit_tree.move(k, '', index)
        self.subreddit_tree.heading(col, command=lambda: self._sort_subreddit_tree(col, not reverse))

