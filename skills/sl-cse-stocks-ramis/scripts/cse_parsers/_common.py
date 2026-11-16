"""Helpers shared by CSE parsers."""
import re
from datetime import datetime

NUM = r"-?[\d,]+(?:\.\d+)?"


def num(s):
    return float(s.replace(",", ""))


def ddmmyyyy(s):
    return datetime.strptime(s, "%d/%m/%Y").strftime("%Y-%m-%d")


MON = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}

__all__ = ["NUM", "num", "ddmmyyyy", "MON", "re"]
