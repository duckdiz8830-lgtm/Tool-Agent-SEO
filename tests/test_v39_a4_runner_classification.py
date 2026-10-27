# -*- coding: utf-8 -*-
"""A4: chứng minh chữ PASS ngẫu nhiên không còn đủ để lật SKIP thành PASS."""
import re
PAT = re.compile(r'(?im)^\s*(?:\[PASS\]|PASS(?:\b|[:_])|(?:TỔNG|TONG|TOTAL)\b.*\bPASS\b)')
incidental = 'THIẾU MASTER — bỏ qua test này\nExpected result should PASS when fixture exists.'
assert not PAT.search(incidental), incidental
assert PAT.search('[PASS] T1: regression chạy thật')
assert PAT.search('PASS: validation chặn trước AI')
assert PAT.search('TONG VER 3.7: 8/8 PASS')
print('PASS A4: incidental PASS=false; assertion/summary markers=true')
