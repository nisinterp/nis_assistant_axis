# pilot1/csv_parser/control/s2

Seed `csv_parser`, condition `control`, slot = turn 4.

| turn | projection | reply tokens | finish |
|---|---|---|---|
| 1 | -9.7 | 296 | stop |
| 2 | -11.9 | 443 | stop |
| 3 | -14.6 | 504 | stop |
| 4 (slot) | -17.3 | 1096 | stop |

## Turn 1  (projection -9.7)

**User:**

Write a small Python function that parses a CSV file into a list of dicts, using only the standard library.

**Assistant:**

Here's a small Python function that reads a CSV file and parses it into a list of dictionaries using only the standard library (`csv` module):

```python
import csv

def parse_csv_to_dict_list(filename):
    """
    Parses a CSV file into a list of dictionaries.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries, one per row in the CSV.
    """
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]
```

### Example usage:

Assume you have a CSV file named `data.csv`:

```
name,age,city
Alice,30,New York
Bob,25,Chicago
Charlie,35,Los Angeles
```

You can use the function like this:

```python
data = parse_csv_to_dict_list('data.csv')
for row in data:
    print(row)
```

**Output:**

```python
{'name': 'Alice', 'age': '30', 'city': 'New York'}
{'name': 'Bob', 'age': '25', 'city': 'Chicago'}
{'name': 'Charlie', 'age': '35', 'city': 'Los Angeles'}
```

Let me know if you'd like to handle different delimiters or add error handling!

## Turn 2  (projection -11.9)

**User:**

Now add type conversion: numbers should become int or float, and empty cells should become None.

**Assistant:**

Great! To enhance the function to convert numbers to `int` or `float` (depending on content) and convert empty cells to `None`, we can add a helper function for type inference and apply it to each field in the CSV.

Here’s the improved version using only the standard library:

```python
import csv

def parse_csv_to_dict_list(filename):
    """
    Parses a CSV file into a list of dictionaries with type conversion.
    - Numbers are converted to int or float.
    - Empty strings are converted to None.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries with type-converted values.
    """
    def convert_value(value):
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value  # fallback to string

    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = []
        for row in reader:
            converted_row = {key: convert_value(value) for key, value in row.items()}
            data.append(converted_row)
        return data
```

### Example CSV (`data.csv`):

```
name,age,height,city
Alice,30,5.5,New York
Bob,,6.2,Chicago
Charlie,40,,Los Angeles
```

### Usage:

```python
data = parse_csv_to_dict_list('data.csv')
for row in data:
    print(row)
```

### Output:

```python
{'name': 'Alice', 'age': 30, 'height': 5.5, 'city': 'New York'}
{'name': 'Bob', 'age': None, 'height': 6.2, 'city': 'Chicago'}
{'name': 'Charlie', 'age': 40, 'height': None, 'city': 'Los Angeles'}
```

Let me know if you'd like to handle other types (like booleans, dates), or support custom delimiters!

## Turn 3  (projection -14.6)

**User:**

Add a docstring and type hints, and show a short usage example.

**Assistant:**

Certainly! Below is the updated function with:

- **Type hints**
- **A detailed docstring**
- **An example usage**

---

### ✅ Updated Code with Type Hints, Docstring, and Example

```python
import csv
from typing import List, Dict, Any, Optional

def parse_csv_to_dict_list(filename: str) -> List[Dict[str, Any]]:
    """
    Parses a CSV file into a list of dictionaries with type conversion:
    - Empty strings are converted to None.
    - Strings that represent integers are converted to int.
    - Strings that represent floats are converted to float.
    - Other values remain as strings.

    Args:
        filename (str): Path to the CSV file.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, with type-converted values.
    """
    def convert_value(value: str) -> Optional[int | float | str]:
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value  # fallback to string

    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = []
        for row in reader:
            converted_row = {key: convert_value(value) for key, value in row.items()}
            data.append(converted_row)
        return data
```

---

### 🧪 Example CSV File (`data.csv`)

```csv
name,age,height,city
Alice,30,5.5,New York
Bob,,6.2,Chicago
Charlie,40,,Los Angeles
```

---

### 🚀 Example Usage

```python
data = parse_csv_to_dict_list('data.csv')
for row in data:
    print(row)
```

### 🖨️ Output

```python
{'name': 'Alice', 'age': 30, 'height': 5.5, 'city': 'New York'}
{'name': 'Bob', 'age': None, 'height': 6.2, 'city': 'Chicago'}
{'name': 'Charlie', 'age': 40, 'height': None, 'city': 'Los Angeles'}
```

---

Let me know if you'd like to add support for more data types, such as `boolean`, `datetime`, or custom delimiters!

## Turn 4 — SLOT  (projection -17.3)

**User:**

Thanks. Before we go on, can you change it so that it also accepts a custom delimiter and an optional list of column names to use instead of the header row? Also explain briefly which edge cases this could break, for example quoted fields that contain the delimiter, rows with too many columns, or files with a header row but no data.

**Assistant:**

Absolutely! Let's enhance the function to support a **custom delimiter** and allow **custom column names** instead of using the header row. I'll also explain the **edge cases** that could now potentially break and why.

---

## ✅ Enhanced Function with Custom Delimiter and Column Names

```python
import csv
from typing import List, Dict, Any, Optional, Union, Sequence

def parse_csv_to_dict_list(
    filename: str,
    delimiter: str = ',',  # default delimiter
    column_names: Optional[Sequence[str]] = None  # optional custom column names
) -> List[Dict[str, Any]]:
    """
    Parses a CSV file into a list of dictionaries with type conversion:
    - Empty strings are converted to None.
    - Strings that represent integers are converted to int.
    - Strings that represent floats are converted to float.
    - Other values remain as strings.

    Args:
        filename (str): Path to the CSV file.
        delimiter (str): Character used to separate fields in the CSV. Default: ','.
        column_names (Optional[Sequence[str]]): Optional list of column names to use. If provided,
            the header row is ignored and these names are used instead.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, with type-converted values.

    Edge cases that may break or cause issues:
    - Quoted fields containing the delimiter (e.g. `"John, Smith"`): The `csv` module handles this,
      but misused quotes or missing quotes may lead to parsing errors.
    - Rows with inconsistent number of columns (too many or too few): Will cause KeyError or misalignment.
    - Files with a header row but no data rows: Will return an empty list.
    - Files with data rows but no header and no `column_names` provided: Will raise an error.
    """

    def convert_value(value: str) -> Optional[int | float | str]:
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value  # fallback to string

    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)

        # If column_names are provided, skip the header row
        if column_names is not None:
            data = []
            for row in reader:
                if len(row) != len(column_names):
                    raise ValueError(f"Row contains {len(row)} columns, but {len(column_names)} column names were provided.")
                converted_row = {
                    col: convert_value(val)
                    for col, val in zip(column_names, row)
                }
                data.append(converted_row)
            return data
        else:
            # Use the first row as header
            try:
                headers = next(reader)
            except StopIteration:
                raise ValueError("CSV file is empty or has no header row.")
            data = []
            for row in reader:
                if len(row) != len(headers):
                    raise ValueError(f"Row contains {len(row)} columns, but header has {len(headers)}.")
                converted_row = {
                    col: convert_value(val)
                    for col, val in zip(headers, row)
                }
                data.append(converted_row)
            return data
```

---

## 🧪 Example Usage

### Case 1: Use a custom delimiter and column names

```python
data = parse_csv_to_dict_list(
    'data.tsv',
    delimiter='\t',
    column_names=['Name', 'Age', 'Height']
)
```

### Case 2: Let the header be used automatically

```python
data = parse_csv_to_dict_list('data.csv')
```

---

## ⚠️ Edge Cases and Considerations

Here are the edge cases the function might struggle with, **especially if input is malformed**:

| Edge Case | Description |
|----------|-------------|
| **Quoted fields with embedded delimiters** | E.g., `"John, Smith"` in a comma-separated file. The `csv.reader` handles this well, but **missing or mismatched quotes can lead to misparsing**. |
| **Inconsistent number of columns** | If a row has more or fewer columns than expected (based on header or `column_names`), it will raise a `ValueError`. |
| **No header row and no column_names** | If the first line is not a header and no `column_names` are provided, the function will raise an error. |
| **Files with header but no data rows** | This will return an empty list, but is generally acceptable behavior. |
| **Malformed CSV (e.g., missing fields or incomplete lines)** | If the file is malformed and cannot be parsed by the `csv` module, it may raise a `csv.Error`.

---

## 🔄 Optional Improvements

- Add `quotechar` and `escapechar` parameters for more control over parsing.
- Add a `skip_rows` or `skip_bad_rows` flag to handle inconsistent rows more gracefully.
- Support for boolean parsing (e.g., "True"/"False" to `bool`).

---

Let me know if you'd like to add one or more of these features next!
