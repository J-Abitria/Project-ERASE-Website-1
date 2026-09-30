from calendar import HTMLCalendar
from datetime import datetime, date
from html import escape
from django.utils.translation import gettext as _


class EventCalendar(HTMLCalendar):
    """Custom HTMLCalendar that displays events on specific dates"""

    def formatweekday(self, day):
        names = [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')]
        return f'<th class="{self.cssclasses_weekday_head[day]}">{names[day]}</th>'
    
    def __init__(self, events=None):
        """
        Initialize calendar with optional events dictionary
        """
        super().__init__()
        self.events = events or {}
    
    def formatday(self, day, weekday):
        """
        Return HTML for a single day cell
        
        Args:
            day: Day of month (0 for days outside month)
            weekday: Weekday number (0-6)
            events_for_day: List of event objects for this day
        """
        if day == 0:
            return '<td class="other-month"></td>'
        
        today = datetime.now().date()
        current_date = datetime(self.year, self.month, day).date()
        is_today = current_date == today
        
        cell_class = 'today' if is_today else ''
        cell_html = f'<td class="{cell_class}">'
        
        # Day number
        day_class = 'day-number-highlight' if is_today else 'day-number'
        cell_html += f'<div class="{day_class}">{day}</div>'

        for event in self.events.get(current_date, []):
            time_str = event.time.strftime('%I:%M %p').lstrip('0')
            cell_html += (
                f'<div class="event-pill" '
                f'data-event-id="{event.pk}" '
                f'data-title="{escape(event.title)}" '
                f'data-time="{escape(time_str)}" '
                f'data-description="{escape(event.description)}" '
                f'data-has-rsvp="{str(event.hasRSVP).lower()}" '
                f'onclick="openEventDetailModal(this)">'
                f'<span class="event-time">{escape(time_str)}</span> '
                f'<span class="event-title">{escape(event.title)}</span>'
                f'</div>'
            )
        
        cell_html += '</td>'
        return cell_html
    
    def formatweek(self, theweek):
        """Return HTML for a week (row)"""
        s = ''.join(self.formatday(d, wd)
                    for (d, wd) in theweek)
        return f'<tr>{s}</tr>'
    
    def formatmonth(self, theyear, themonth, withyear=True):
        """Return formatted month calendar"""
        self.year = theyear
        self.month = themonth
        
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="calendar-table">')
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)


def resolve_month_year(year=None, month=None):
    """
    Parse and validate year and month inputs, defaulting to the current date.
    
    Returns:
        tuple: (resolved_year: int, resolved_month: int)
    """
    now = datetime.now()
    try:
        y = int(year) if year is not None else now.year
        m = int(month) if month is not None else now.month
        if not (1 <= m <= 12):
            m = now.month
            y = now.year
    except (ValueError, TypeError):
        y, m = now.year, now.month
    return y, m


def get_navigation_dates(year, month):
    """
    Calculate previous and next month/year navigation coordinates and display date.
    """
    display_date = date(year, month, 1)
    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year

    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year

    return {
        'display_date': display_date,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }


def get_calendar_html(year, month, events=None):
    """
    Generate calendar HTML for a specific month.
    
    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
        events: Dictionary of events with date objects as keys
    
    Returns:
        HTML string for the calendar
    """
    calendar = EventCalendar(events=events)
    return calendar.formatmonth(year, month)


def get_calendar_data(year=None, month=None, events=None):
    """
    Build full calendar rendering context including HTML and navigation coordinates.
    """
    resolved_year, resolved_month = resolve_month_year(year, month)
    nav_dates = get_navigation_dates(resolved_year, resolved_month)
    calendar_html = get_calendar_html(resolved_year, resolved_month, events=events)

    return {
        'current_year': resolved_year,
        'current_month': resolved_month,
        'calendar_html': calendar_html,
        **nav_dates,
    }
