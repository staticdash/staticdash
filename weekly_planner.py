"""
Weekly Planner/Calendar Generator using StaticDash
Generates a weekly planner with one page per week, showing correct dates for any year.
"""

from staticdash import Page, Dashboard
from datetime import datetime, timedelta
import calendar

def generate_weekly_planner(year=None, num_weeks=52):
    """
    Generate a weekly planner dashboard with one page per week.
    
    Args:
        year: The year for the planner (defaults to current year)
        num_weeks: Number of weeks to generate (default 52)
    """
    if year is None:
        year = datetime.now().year
    
    # Create the dashboard
    dashboard = Dashboard(
        title=f"Weekly Planner {year}",
        page_width=1000
    )
    
    # Start from the first Monday of the year (or close to it)
    jan1 = datetime(year, 1, 1)
    # Find the first Monday
    days_to_monday = (7 - jan1.weekday()) % 7
    if days_to_monday > 0:
        first_monday = jan1 + timedelta(days=days_to_monday)
    else:
        first_monday = jan1
    
    # Generate pages for each week
    for week_num in range(1, num_weeks + 1):
        week_start = first_monday + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)
        
        # Format week title
        week_title = f"Week {week_num}: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}"
        page_slug = f"week{week_num:02d}"
        
        # Create page for this week
        page = Page(page_slug, week_title)
        
        # Build the calendar HTML with inline styles
        calendar_html = '''
<style>
@media print {
    #sidebar { display: none !important; }
    #content { margin-left: 0 !important; }
    .floating-header, .floating-footer { display: none !important; }
    .calendar-week { page-break-inside: avoid; }
    .notes-box { page-break-inside: avoid; }
}

.calendar-week {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 12px;
    margin: 20px 0;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 12px;
}

.calendar-day {
    border: 3px solid #2c3e50;
    border-radius: 10px;
    padding: 16px;
    min-height: 280px;
    background: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    transition: transform 0.2s, box-shadow 0.2s;
}

.calendar-day:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
}

.day-header {
    font-weight: bold;
    font-size: 1.15em;
    color: white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 6px;
    padding: 10px 12px;
    margin: -16px -16px 12px -16px;
    text-align: center;
    letter-spacing: 0.5px;
}

.day-date {
    font-size: 0.95em;
    color: #6c757d;
    margin-bottom: 18px;
    text-align: center;
    font-weight: 500;
    padding-bottom: 12px;
    border-bottom: 2px solid #e9ecef;
}

.day-content {
    min-height: 160px;
    color: #495057;
    line-height: 1.8;
}

.notes-box {
    grid-column: 1 / -1;
    border: 3px solid #2c3e50;
    border-radius: 10px;
    padding: 24px;
    min-height: 200px;
    background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
    margin-top: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.15);
}

.notes-header {
    font-weight: bold;
    font-size: 1.4em;
    color: #2c3e50;
    border-bottom: 3px solid #d63031;
    padding-bottom: 10px;
    margin-bottom: 18px;
    text-align: center;
    letter-spacing: 1px;
}

.notes-content {
    min-height: 140px;
    color: #2c3e50;
    line-height: 1.8;
}
</style>
<div class="calendar-week">'''
        
        # Create boxes for each day of the week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day_name in enumerate(days):
            current_date = week_start + timedelta(days=i)
            day_html = f'''
    <div class="calendar-day">
        <div class="day-header">{day_name}</div>
        <div class="day-date">{current_date.strftime('%B %d, %Y')}</div>
        <div class="day-content" style="min-height: 120px;">
            <!-- Space for user to write notes -->
        </div>
    </div>'''
            calendar_html += day_html
        
        calendar_html += '''
</div>
<div class="notes-box">
    <div class="notes-header">&#128221; Weekly Notes</div>
    <div class="notes-content">
        <!-- Space for weekly notes, goals, and reminders -->
    </div>
</div>
'''
        
        # Add as raw HTML element
        page.elements.append(("raw_html", calendar_html, None))
        
        # Add the page to the dashboard
        dashboard.add_page(page)
    
    return dashboard


if __name__ == "__main__":
    # Generate planner for the current year with 52 weeks
    planner = generate_weekly_planner(year=2025, num_weeks=52)
    
    # Publish the dashboard
    planner.publish(output_dir="weekly_planner_output")
    
    print("✅ Weekly planner generated successfully!")
    print("📁 Open weekly_planner_output/index.html to view your planner")
