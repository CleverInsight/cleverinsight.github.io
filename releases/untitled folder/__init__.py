import os
import calendar
import pandas as pd
from glob import glob
from calendar import monthrange
from datetime import datetime, timedelta, date


def get_month_day_range(date):
    """
    For a date 'date' returns the start and end date for the month of 'date'.

    Month with 31 days:
    >>> date = datetime.date(2011, 7, 27)
    >>> get_month_day_range(date)
    (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

    Month with 28 days:
    >>> date = datetime.date(2011, 2, 15)
    >>> get_month_day_range(date)
    (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
    """
    first_day = date.replace(day = 1)
    last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
    return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')


def get_weekly_range():
    """
    Gets the weekly range.
    
    :returns:   The weekly range.
    :rtype:     { return_type_description }
    """
    today = date.today()
    day = today.strftime("%d/%m/%Y")
    dt = datetime.strptime(day, '%d/%m/%Y')
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)

    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')



def get_last_seven_days():
    """
    Gets the last seven days.
    
    :returns:   The last seven days.
    :rtype:     { return_type_description }
    """
    end = date.today()
    start = end - timedelta(5)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')


def last_day_of_month(date_value):
    """
    Get last day of current month
    
    :param      date_value:  The date value
    :type       date_value:  { type_description }
    
    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    return date_value.replace(day = monthrange(date_value.year, date_value.month)[1])


def get_monthly_range():
    """
    Gets the monthly range.
    
    :returns:   The monthly range.
    :rtype:     { return_type_description }
    """
    today = date.today()
    first_day = today.replace(day=1)
    last_day = last_day_of_month(today)
    return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')



def get_yearly_range():
    
    current_year = date.today().year
    start_date = str(current_year) + "-01-01"
    end_date = str(current_year) + "-12-31"
    return start_date, end_date


def date_between(start, end):
    """
    Returns list of all dates between given `start and end`
    
    :param      start:  Start date
    :type       start:  { type_description }
    :param      end:    End Date
    :type       end:    { type_description }
    
    :returns:   { list of all dates range }
    :rtype:     { return_type_description }
    """
    d1 = datetime.strptime(start, '%Y-%m-%d')
    d2 = datetime.strptime(end, '%Y-%m-%d')
    diff = d2 - d1
    return [(d1 + timedelta(i)).strftime('%Y-%m-%d') for i in range(diff.days + 1)]



def generate_multiple_filepath(location, start, end):
    """
    Generate Multiple Filepath
    
    :param      location:  The location
    :type       location:  { type_description }
    :param      start:     The start
    :type       start:     { type_description }
    :param      end:       The end
    :type       end:       { type_description }
    
    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    all_dates = date_between(start, end)
    all_files = []

    for _d in all_dates:

        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), location, _d + '.csv')):
            all_files.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), location, _d + '.csv'))

    return all_files



def combine(location, start, end):
    """
    Combine given list of all files.
    
    :param      files:  The files
    :type       files:  { type_description }
    
    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    path = os.path.join('data', location)

    files = generate_multiple_filepath(path, start, end)

    return pd.concat([pd.read_csv(file).dropna(how='all') for file in files])
