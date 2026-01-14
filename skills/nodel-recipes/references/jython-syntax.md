# Jython 2.5 Syntax Reference

Nodel recipes run on Jython 2.5.4 (Python 2.5 syntax on JVM). This reference covers syntax differences from modern Python.

## Critical Syntax Differences

### Exception Handling

```python
# CORRECT - Python 2.5 syntax
try:
    result = risky_operation()
except Exception, e:
    console.error('Failed: %s' % e)

# WRONG - Python 3 syntax
try:
    result = risky_operation()
except Exception as e:  # SyntaxError!
    console.error(f'Failed: {e}')  # f-strings don't exist!
```

### String Formatting

```python
# CORRECT - % formatting (always works)
message = 'Device %s at port %d' % (name, port)
message = 'Status: %(level)s - %(message)s' % {'level': 0, 'message': 'OK'}

# WRONG - f-strings (Python 3.6+)
message = f'Device {name} at port {port}'  # SyntaxError!

# WRONG - .format() (Python 2.6+)
message = 'Device {} at port {}'.format(name, port)  # AttributeError - method doesn't exist in 2.5
```

### Print Statement

```python
# CORRECT - Use console methods
console.info('Message here')
console.log('Debug message')

# Avoid print (behavior varies)
print 'old style'  # Python 2 syntax
print('function style')  # Works but prefer console
```

### Integer Division

```python
# In Python 2, / is integer division for integers
result = 5 / 2  # Returns 2, not 2.5

# For float division
result = 5.0 / 2  # Returns 2.5
result = float(5) / 2  # Returns 2.5
```

### Dictionary Methods

```python
# CORRECT - Python 2 style
for key in mydict.keys():
    pass
for key, value in mydict.items():
    pass

# dict.iteritems() available but items() is fine
# dict.viewitems() does NOT exist
```

### Limited `with` Statement Support

```python
# The with statement requires a future import in Python 2.5
from __future__ import with_statement

# Then you can use it
with open('file.txt') as f:
    content = f.read()

# Alternative without import - use try/finally
f = open('file.txt')
try:
    content = f.read()
finally:
    f.close()
```

**Note:** In Nodel recipes, prefer try/finally for compatibility, or verify `with` works in your Jython version.

### Class Definitions

```python
# Inherit from object for new-style classes
class MyClass(object):
    def __init__(self):
        pass

# Old-style class (avoid)
class OldStyle:
    pass
```

### No Set Literals

```python
# CORRECT
my_set = set([1, 2, 3])

# WRONG - Set literals (Python 2.7+)
my_set = {1, 2, 3}  # SyntaxError in Python 2.5
```

### No Dictionary Comprehensions

```python
# CORRECT - Use dict()
result = dict((k, v*2) for k, v in items)

# WRONG - Dict comprehensions (Python 2.7+)
result = {k: v*2 for k, v in items}  # SyntaxError!
```

### Conditional Expressions

```python
# CORRECT - Ternary exists in 2.5
result = 'on' if power else 'off'
```

### Lambda Functions

```python
# Lambdas work but have limitations
process = lambda x: x * 2

# For complex logic, use def
def process(x):
    if x > 0:
        return x * 2
    return 0
```

## Available Built-ins

### Safe to Use

- `len()`, `range()`, `enumerate()`
- `str()`, `int()`, `float()`, `bool()`
- `list()`, `dict()`, `tuple()`, `set()`
- `map()`, `filter()`, `reduce()` (reduce is built-in)
- `sorted()`, `reversed()`
- `min()`, `max()`, `sum()`
- `abs()`, `round()`
- `isinstance()`, `type()`
- `getattr()`, `setattr()`, `hasattr()`

### JSON Handling

```python
# Nodel provides json helpers
obj = json_decode('{"key": "value"}')
text = json_encode({'key': 'value'})

# Don't try to import json module
```

### Avoid / Unavailable

- `collections.OrderedDict` - Not in 2.5
- `collections.Counter` - Not in 2.5
- `argparse` - Not in 2.5
- `logging` module - Use console instead
- `subprocess` - Use Process/quick_process instead
- `urllib2` - Use get_url instead

## Common Patterns

### Safe Dictionary Access

```python
# Get with default
value = mydict.get('key', 'default')

# Check existence
if 'key' in mydict:
    value = mydict['key']
```

### List Operations

```python
# Append
items.append(value)

# Extend
items.extend([1, 2, 3])

# Insert at position
items.insert(0, value)

# Remove
items.remove(value)
del items[0]
```

### String Operations

```python
# Split and join
parts = 'a,b,c'.split(',')
result = ','.join(parts)

# Strip whitespace
clean = '  text  '.strip()

# Find substring
pos = text.find('needle')  # Returns -1 if not found
if 'needle' in text:
    pass

# Replace
result = text.replace('old', 'new')

# Case conversion
upper = text.upper()
lower = text.lower()
```

### None Checks

```python
# Check for None
if value is None:
    pass
if value is not None:
    pass

# Truthy check (includes None, empty string, 0, empty list)
if value:
    pass
if not value:
    pass
```
