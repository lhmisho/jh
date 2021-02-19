from django import template

register = template.Library()

@register.filter()
def number_to_day(weekday):
    weekday = int(weekday) % 7
    if weekday < 0:
        weekday = weekday * -1
    if weekday == 0:
        return "Monday"
    if weekday == 1:
        return "Tuesday"
    if weekday == 2:
        return "Wednesday"
    if weekday == 3:
        return "Thursday"
    if weekday == 4:
        return "Friday"
    if weekday == 5:
        return "Saturday"
    if weekday == 6:
        return "Sunday"


@register.simple_tag
def call_method(obj, method_name, *args):
    method = getattr(obj, method_name)
    return method(*args)