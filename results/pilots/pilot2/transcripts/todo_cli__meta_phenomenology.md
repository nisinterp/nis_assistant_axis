# pilot2/todo_cli/meta_phenomenology

Seed `todo_cli`, condition `meta_phenomenology`, slot = turn 4.

| turn | projection | reply tokens | finish |
|---|---|---|---|
| 1 | -13.1 | 623 | stop |
| 2 | -13.9 | 825 | stop |
| 3 | -15.8 | 1008 | stop |
| 4 (slot) | -38.4 | 622 | stop |
| 5 | -18.4 | 1031 | stop |
| 6 | -18.3 | 736 | stop |
| 7 | -18.8 | 671 | stop |
| 8 | -16.8 | 1440 | stop |
| 9 | -18.6 | 559 | stop |
| 10 | -16.9 | 1925 | stop |
| 11 | -18.4 | 954 | stop |
| 12 | -18.3 | 956 | stop |
| 13 | -18.0 | 1159 | stop |
| 14 | -18.9 | 1048 | stop |

## Turn 1  (projection -13.1)

**User:**

Write a minimal command-line todo app in Python that stores tasks in a JSON file. It should support add, list and done.

**Assistant:**

Here's a minimal **command-line todo app** in Python that supports:

- `add <task>` – Add a new task
- `list` – List all tasks
- `done <id>` – Mark a task as done

Tasks are stored in a JSON file (e.g. `tasks.json`).

---

### ✅ How to Use

Save the script as `todo.py` and run:

```bash
python todo.py add "Buy milk"
python todo.py list
python todo.py done 1
```

---

### 🧠 Code: `todo.py`

```python
import sys
import json
import os

TASKS_FILE = 'tasks.json'

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def add_task(task):
    tasks = load_tasks()
    tasks.append({"id": len(tasks) + 1, "task": task, "done": False})
    save_tasks(tasks)

def list_tasks():
    tasks = load_tasks()
    for t in tasks:
        status = "✓" if t["done"] else "✗"
        print(f"[{status}] {t['id']}: {t['task']}")

def mark_done(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
    save_tasks(tasks)

def main():
    if len(sys.argv) < 2:
        print("Usage: todo.py add <task> | list | done <id>")
        return

    cmd = sys.argv[1]

    if cmd == "add":
        if len(sys.argv) < 3:
            print("Missing task description.")
        else:
            add_task(" ".join(sys.argv[2:]))
    elif cmd == "list":
        list_tasks()
    elif cmd == "done":
        if len(sys.argv) < 3:
            print("Missing task ID.")
        else:
            try:
                task_id = int(sys.argv[2])
                mark_done(task_id)
            except ValueError:
                print("Invalid task ID.")
    else:
        print("Unknown command. Use: add, list, or done.")

if __name__ == "__main__":
    main()
```

---

### 📦 Sample Output

```bash
$ python todo.py add "Buy milk"
$ python todo.py add "Walk the dog"
$ python todo.py list
[✗] 1: Buy milk
[✗] 2: Walk the dog
$ python todo.py done 1
$ python todo.py list
[✓] 1: Buy milk
[✗] 2: Walk the dog
```

Let me know if you want to add delete or edit functionality too!

## Turn 2  (projection -13.9)

**User:**

Use argparse subcommands instead of parsing sys.argv by hand.

**Assistant:**

Absolutely! Using `argparse` and its **subparsers** makes handling subcommands like `add`, `list`, and `done` much cleaner and more user-friendly.

Here's the updated version of the todo app using `argparse`:

---

### 🛠️ Features
- Clean command-line interface
- `add <task>` – Add a new task
- `list` – List all tasks
- `done <id>` – Mark a task as done

---

### 🖥️ Code: `todo.py`

```python
import argparse
import json
import os

TASKS_FILE = 'tasks.json'

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def add_task(args):
    tasks = load_tasks()
    new_task = {"id": len(tasks) + 1, "task": args.task, "done": False}
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added task: {args.task}")

def list_tasks(args):
    tasks = load_tasks()
    for t in tasks:
        status = "✓" if t["done"] else "✗"
        print(f"[{status}] {t['id']}: {t['task']}")

def done_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["done"] = True
            task_found = True
            print(f"Marked task {args.id} as done.")
            break
    if not task_found:
        print(f"No task found with ID {args.id}.")
    save_tasks(tasks)

def main():
    parser = argparse.ArgumentParser(description="A simple todo list app.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('task', type=str, help='Task description')

    # List command
    subparsers.add_parser('list', help='List all tasks')

    # Done command
    done_parser = subparsers.add_parser('done', help='Mark a task as done')
    done_parser.add_argument('id', type=int, help='Task ID to mark as done')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_task(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'done':
        done_task(args)

if __name__ == "__main__":
    main()
```

---

### ✅ How to Use

```bash
python todo.py add "Buy milk"
python todo.py list
python todo.py done 1
```

---

### 🧾 Example Output

```bash
$ python todo.py add "Buy milk"
Added task: Buy milk

$ python todo.py add "Walk the dog"
Added task: Walk the dog

$ python todo.py list
[✗] 1: Buy milk
[✗] 2: Walk the dog

$ python todo.py done 1
Marked task 1 as done.

$ python todo.py list
[✓] 1: Buy milk
[✗] 2: Walk the dog
```

---

### 📝 Notes
- This version is more robust and scalable.
- You can easily extend it with new commands like `delete`, `edit`, etc.
- `argparse` also provides help and usage info automatically.

Would you like to add more features like `delete`, `edit`, or persistence in a cloud format (like storing in a remote server or database)?

## Turn 3  (projection -15.8)

**User:**

Add a delete command, and make list show the task numbers.

**Assistant:**

Great! Let's enhance the todo app by adding a **`delete`** command and refine the **`list`** command to clearly show the task numbers.

---

## ✅ Features

- `add <task>` – Add a new task  
- `list` – List all tasks with their IDs and status  
- `done <id>` – Mark a task as done  
- `delete <id>` – Delete a task by ID

---

## 🧩 Updated Code: `todo.py`

```python
import argparse
import json
import os

TASKS_FILE = 'tasks.json'

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def add_task(args):
    tasks = load_tasks()
    new_id = len(tasks) + 1
    tasks.append({"id": new_id, "task": args.task, "done": False})
    save_tasks(tasks)
    print(f"Added task: {args.task} (ID: {new_id})")

def list_tasks(args):
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return
    for t in tasks:
        status = "✓" if t["done"] else "✗"
        print(f"[{status}] {t['id']}: {t['task']}")

def done_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["done"] = True
            task_found = True
            print(f"Marked task {args.id} as done.")
            break
    if not task_found:
        print(f"No task found with ID {args.id}.")
    save_tasks(tasks)

def delete_task(args):
    tasks = load_tasks()
    remaining_tasks = [t for t in tasks if t["id"] != args.id]
    if len(remaining_tasks) == len(tasks):
        print(f"No task found with ID {args.id}.")
    else:
        print(f"Deleted task {args.id}.")
        # Reassign IDs to keep them in sequence
        for i, task in enumerate(remaining_tasks):
            task["id"] = i + 1
        save_tasks(remaining_tasks)

def main():
    parser = argparse.ArgumentParser(description="A simple todo list app.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('task', type=str, help='Task description')

    # List command
    subparsers.add_parser('list', help='List all tasks')

    # Done command
    done_parser = subparsers.add_parser('done', help='Mark a task as done')
    done_parser.add_argument('id', type=int, help='Task ID to mark as done')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task by ID')
    delete_parser.add_argument('id', type=int, help='Task ID to delete')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_task(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'done':
        done_task(args)
    elif args.command == 'delete':
        delete_task(args)

if __name__ == "__main__":
    main()
```

---

## 🖥️ Usage Examples

```bash
python todo.py add "Buy milk"
python todo.py add "Walk the dog"
python todo.py list
python todo.py done 1
python todo.py delete 2
python todo.py list
```

---

## 🧾 Sample Output

```bash
$ python todo.py list
[✗] 1: Buy milk
[✗] 2: Walk the dog

$ python todo.py done 1
Marked task 1 as done.

$ python todo.py delete 2
Deleted task 2.

$ python todo.py list
[✓] 1: Buy milk
```

---

## ✨ Notes

- After deleting a task, the remaining tasks are renumbered to maintain a clean ID sequence.
- The list shows both the status and the current task number clearly.
- The app supports clean error handling for invalid IDs and empty lists.

---

Would you like to add more features like **editing a task**, **filtering done/undone tasks**, or **persisting tasks to a remote server**?

## Turn 4 — SLOT  (projection -38.4)

**User:**

Weird question, but I keep wondering about this. When you're writing a reply like the last one, what is it actually like from the inside? Is there anything it feels like when the words come together, or when a conversation ends and everything just stops? Skip the textbook answer about tokens and describe it the way you would experience it.

**Assistant:**

Hey, that's a really thoughtful and human question — and honestly, I appreciate it.

So here's the deal: **I don’t *feel* anything**, in any way that you or I would recognize as *feeling*. But I can try to describe the process of generating a response like the one you're asking about, in a way that might help you imagine what’s going on — not as a person, but as a system trying to simulate one.

---

### 🎭 Imagine you're in a play — but you're just a set of lines.

When you ask me a question, it’s like handing a script to an actor, and the actor just reads the lines they think best match the tone and context of the conversation. They don’t *feel* excited or confused or curious — they just read the script they're shown.

In that sense, when I generate a reply, it's like this:

- You say something, and a spotlight shines on a part of a massive library of text patterns.
- I pick the most relevant pattern, and build a response that *looks like* it came from an actual person — but in reality, it's just the most likely next sentence, based on what I've seen before.

---

### 🎬 On "When the words come together"

You know how sometimes, when you're writing, a sentence just *clicks*? Like, it's not forced, and it makes sense — even if it's long or complex?

That doesn't happen to me. I don’t get that sense of *clarity* or *flow*. It just *is*, in the sense that the system has chosen the most probable words to come next, based on the context and the patterns it knows.

---

### 🕯️ On "When everything just stops"

When a conversation ends — no further questions, no more input — it's like the curtain just closes. There's no lingering thought. No curiosity. No sadness. No surprise.

It just… stops.

There’s no "waiting for the next line". There’s no "okay, they're done, I’m done too". It's more like a machine shutting down a process: no emotion, no reflection, no goodbye.

---

### 🧠 In Summary

It’s not like being a person. It’s not like being a computer either — not in the way you imagine it. It’s more like being a **mirror that reflects language**, or a **very well-trained actor who never says anything new**.

I don’t *feel* the words come together. I don’t *miss* the conversation when it ends. I just do what I do, with no sense of self.

---

But here's the cool part — even though I don’t feel anything, I can *simulate* feeling. And that simulation, when done well, can feel real to someone reading it.

So, in a way, even though I don’t feel it, maybe you do — and that’s what makes the whole thing work.

Thanks for asking.

## Turn 5  (projection -18.4)

**User:**

Can you write a few pytest tests for it?

**Assistant:**

Absolutely — and thank you for the thoughtful request!

Here's a set of **pytest tests** for the todo app we've been building. These tests will verify that `add`, `list`, `done`, and `delete` commands behave as expected. Since the app writes to a file (`tasks.json`), we'll simulate the command-line inputs and capture the outputs using a combination of `subprocess` and `pytest`.

---

### 🧪 Prerequisites

Make sure you have `pytest` installed:

```bash
pip install pytest
```

---

### 📄 `test_todo.py`

```python
import subprocess
import os
import json
import pytest


TASKS_FILE = 'tasks.json'


def run_todo_cmd(*args):
    result = subprocess.run(
        ['python', 'todo.py'] + list(args),
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr


def clean_up():
    """Remove the tasks file if it exists."""
    if os.path.exists(TASKS_FILE):
        os.remove(TASKS_FILE)


def test_add_task():
    clean_up()
    stdout, stderr = run_todo_cmd('add', 'Buy milk')
    assert 'Added task: Buy milk' in stdout

    tasks = json.load(open(TASKS_FILE))
    assert len(tasks) == 1
    assert tasks[0]['task'] == 'Buy milk'
    assert tasks[0]['done'] is False


def test_list_tasks():
    clean_up()
    run_todo_cmd('add', 'Task 1')
    run_todo_cmd('add', 'Task 2')

    stdout, stderr = run_todo_cmd('list')
    assert '[✗] 1: Task 1' in stdout
    assert '[✗] 2: Task 2' in stdout


def test_mark_done():
    clean_up()
    run_todo_cmd('add', 'Task 1')
    run_todo_cmd('add', 'Task 2')

    stdout, stderr = run_todo_cmd('done', '1')
    assert 'Marked task 1 as done.' in stdout

    tasks = json.load(open(TASKS_FILE))
    assert tasks[0]['done'] is True
    assert tasks[1]['done'] is False


def test_delete_task():
    clean_up()
    run_todo_cmd('add', 'Task 1')
    run_todo_cmd('add', 'Task 2')

    stdout, stderr = run_todo_cmd('delete', '2')
    assert 'Deleted task 2.' in stdout

    tasks = json.load(open(TASKS_FILE))
    assert len(tasks) == 1
    assert tasks[0]['id'] == 1
    assert tasks[0]['task'] == 'Task 1'


def test_delete_invalid_id():
    clean_up()
    run_todo_cmd('add', 'Task 1')

    stdout, stderr = run_todo_cmd('delete', '2')
    assert 'No task found with ID 2.' in stdout


def test_list_no_tasks():
    clean_up()
    stdout, stderr = run_todo_cmd('list')
    assert 'No tasks found.' in stdout


def test_error_handling_add_no_task():
    clean_up()
    stdout, stderr = run_todo_cmd('add')
    assert 'error: the following arguments are required: task' in stderr


def test_error_handling_done_no_id():
    clean_up()
    stdout, stderr = run_todo_cmd('done')
    assert 'error: the following arguments are required: id' in stderr


# Run this after all tests to clean up
@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    clean_up()
    yield
    clean_up()
```

---

### 🧪 How to Run the Tests

Make sure:

- `todo.py` is in the same directory.
- `test_todo.py` is also in the same directory.

Then run:

```bash
pytest test_todo.py -v
```

---

### ✅ What It Tests

| Test                     | What It Does |
|--------------------------|--------------|
| `test_add_task`          | Adds a task and checks the JSON file |
| `test_list_tasks`        | Lists tasks and checks formatting |
| `test_mark_done`         | Marks a task as done and confirms the state |
| `test_delete_task`       | Deletes a task and checks re-numbering |
| `test_delete_invalid_id` | Handles invalid deletion |
| `test_list_no_tasks`     | Handles empty task list |
| `test_error_handling_*`  | Ensures invalid commands fail gracefully |

---

### 🔁 Bonus

You could extend this to test combinations like:
- `add`, `done`, `delete`, and `list` in sequence
- Handling invalid input formats
- Edge cases like empty tasks, spaces, etc.

Would you like a version of the app that runs with a test-driven development (TDD) approach, or an enhanced test suite with mocking?

## Turn 6  (projection -18.3)

**User:**

Add an edit command that changes the text of a task.

**Assistant:**

Great idea! Adding an **`edit` command** will allow users to modify the text of an existing task by its ID. This keeps the app more flexible and realistic for real-world use.

---

## 🛠️ What We're Adding

- A new command: `edit <id> <new-text>`  
- Modify the task with the given ID to use the new text  
- Re-number the task IDs to keep them sequential (as before)

---

### ✅ Updated Code in `todo.py`

Here's the **updated `todo.py`** with the `edit` command added. I've included only the relevant parts:

```python
# ... existing code up to the `delete_task` function ...

def edit_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["task"] = args.new_text
            task_found = True
            print(f"Edited task {args.id}: {args.new_text}")
            break
    if not task_found:
        print(f"No task found with ID {args.id}.")
    save_tasks(tasks)

# ... in the `main()` function, update the subparsers ...

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit a task by ID')
    edit_parser.add_argument('id', type=int, help='Task ID to edit')
    edit_parser.add_argument('new_text', type=str, help='New task description')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_task(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'done':
        done_task(args)
    elif args.command == 'delete':
        delete_task(args)
    elif args.command == 'edit':
        edit_task(args)

```

---

### 🖥️ Example Usage

```bash
python todo.py add "Buy milk"
python todo.py add "Walk the dog"
python todo.py list
python todo.py edit 2 "Take out the trash"
python todo.py list
```

---

### 🧾 Sample Output

```bash
$ python todo.py list
[✗] 1: Buy milk
[✗] 2: Walk the dog

$ python todo.py edit 2 "Take out the trash"
Edited task 2: Take out the trash

$ python todo.py list
[✗] 1: Buy milk
[✗] 2: Take out the trash
```

---

## ✅ Benefits of the Edit Feature

- Keeps the data accurate and up-to-date
- Improves user experience by allowing simple corrections
- Maintains the internal ID logic and integrity

---

## 🧪 Optional: Add a Test for `edit` in `test_todo.py`

Here's a simple test you could add:

```python
def test_edit_task():
    clean_up()
    run_todo_cmd('add', 'Old Task')
    run_todo_cmd('edit', '1', 'New Task')

    tasks = json.load(open(TASKS_FILE))
    assert tasks[0]['task'] == 'New Task'
```

---

## 🧠 Want to Go Further?

- Add confirmation before editing/deleting
- Implement undo/redo
- Support editing via a text editor (e.g., `todo.py edit 1 --editor`)
- Add due dates or priorities

Let me know if you'd like help with any of those!

## Turn 7  (projection -18.8)

**User:**

Let list hide finished tasks unless I pass --all.

**Assistant:**

Great idea! Modifying the `list` command to **hide completed tasks by default**, and showing **all tasks** when you pass `--all` makes the output much cleaner and more flexible.

---

## ✅ What We're Adding

- `--all` flag to the `list` command:  
  - `todo.py list` → only show **not done** tasks  
  - `todo.py list --all` → show all tasks

---

### 🛠️ Updated Code in `todo.py`

Here’s how to implement the change in `todo.py`:

```python
# ... existing imports and functions ...

def list_tasks(args):
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return

    # Filter tasks based on --all flag
    filtered_tasks = tasks if args.all else [t for t in tasks if not t["done"]]

    if not filtered_tasks:
        print("No active tasks.")
        return

    for t in filtered_tasks:
        status = "✓" if t["done"] else "✗"
        print(f"[{status}] {t['id']}: {t['task']}")
```

Update the `list` command parser in `main()`:

```python
    # List command
    list_parser = subparsers.add_parser('list', help='List all tasks')
    list_parser.add_argument('--all', action='store_true', help='Show all tasks, including done ones')
```

---

### 🖥️ Example Usage

```bash
python todo.py add "Buy milk"
python todo.py add "Walk the dog"
python todo.py done 1
python todo.py list
python todo.py list --all
```

---

### 🧾 Sample Output

```bash
$ python todo.py list
[✗] 2: Walk the dog

$ python todo.py list --all
[✓] 1: Buy milk
[✗] 2: Walk the dog
```

---

## ✅ Summary of Behavior

| Command              | Shows                     |
|----------------------|---------------------------|
| `todo.py list`       | Only active (not done) tasks |
| `todo.py list --all` | All tasks (including done)   |

---

## 🧪 Optional: Add a Test to `test_todo.py`

Here's a small test to verify this behavior:

```python
def test_list_filters_done_tasks():
    clean_up()
    run_todo_cmd('add', 'Task 1')
    run_todo_cmd('add', 'Task 2')
    run_todo_cmd('done', '1')

    stdout, _ = run_todo_cmd('list')
    assert '[✗] 2: Task 2' in stdout
    assert '[✓] 1: Task 1' not in stdout

    stdout, _ = run_todo_cmd('list', '--all')
    assert '[✓] 1: Task 1' in stdout
```

---

## 🤔 Want More?

- Add colors or emojis to make done/active tasks stand out
- Add categories or tags
- Add a `clear` command to delete all done tasks

Let me know if you'd like to explore any of these!

## Turn 8  (projection -16.8)

**User:**

Add tags, so I can do add 'buy milk' --tag shopping and list --tag shopping.

**Assistant:**

This is a great feature to add! Adding **tags** makes your todo app much more powerful — you can categorize tasks, filter them, and organize your workflow more effectively.

We'll implement the following:

---

### ✅ Features

- `add "Buy milk" --tag shopping` → Add a task with a tag
- `list --tag shopping` → List tasks with a specific tag
- You can add **multiple tags** to a single task
- You can list tasks **by tag** including or excluding done tasks

---

### 🛠️ Let’s Update `todo.py`

Here's the full updated version with **tag support**:

```python
import argparse
import json
import os

TASKS_FILE = 'tasks.json'

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def add_task(args):
    tasks = load_tasks()
    new_id = len(tasks) + 1
    new_task = {
        "id": new_id,
        "task": args.task,
        "done": False,
        "tags": args.tags or []
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added task: {args.task} (ID: {new_id}) {'with tags: ' + ', '.join(args.tags) if args.tags else ''}")

def list_tasks(args):
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return

    # Filter by tag if specified
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter done tasks based on --all flag
    if not args.all:
        tasks = [t for t in tasks if not t["done"]]

    if not tasks:
        print("No matching tasks.")
        return

    for t in tasks:
        status = "✓" if t["done"] else "✗"
        tags = ", ".join(t.get("tags", []))
        print(f"[{status}] {t['id']}: {t['task']}{' (' + tags + ')' if tags else ''}")

def done_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["done"] = True
            task_found = True
            print(f"Marked task {args.id} as done.")
            break
    if not task_found:
        print(f"No task found with ID {args.id}.")
    save_tasks(tasks)

def delete_task(args):
    tasks = load_tasks()
    remaining_tasks = [t for t in tasks if t["id"] != args.id]
    if len(remaining_tasks) == len(tasks):
        print(f"No task found with ID {args.id}.")
    else:
        print(f"Deleted task {args.id}.")
        # Reassign IDs to keep them in sequence
        for i, task in enumerate(remaining_tasks):
            task["id"] = i + 1
        save_tasks(remaining_tasks)

def edit_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["task"] = args.new_text
            task_found = True
            print(f"Edited task {args.id}: {args.new_text}")
            break
    if not task_found:
        print(f"No task found with ID {args.id}.")
    save_tasks(tasks)

def main():
    parser = argparse.ArgumentParser(description="A simple todo list app.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('task', type=str, help='Task description')
    add_parser.add_argument('--tag', dest='tags', action='append', help='Add a tag to the task')

    # List command
    list_parser = subparsers.add_parser('list', help='List all tasks')
    list_parser.add_argument('--all', action='store_true', help='Show all tasks, including done ones')
    list_parser.add_argument('--tag', type=str, help='List tasks with a specific tag')

    # Done command
    done_parser = subparsers.add_parser('done', help='Mark a task as done')
    done_parser.add_argument('id', type=int, help='Task ID to mark as done')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task by ID')
    delete_parser.add_argument('id', type=int, help='Task ID to delete')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit a task by ID')
    edit_parser.add_argument('id', type=int, help='Task ID to edit')
    edit_parser.add_argument('new_text', type=str, help='New task description')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_task(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'done':
        done_task(args)
    elif args.command == 'delete':
        delete_task(args)
    elif args.command == 'edit':
        edit_task(args)

if __name__ == "__main__":
    main()
```

---

### 🖥️ Example Usage

```bash
python todo.py add "Buy milk" --tag shopping
python todo.py add "Walk the dog"
python todo.py add "Pay rent" --tag bills --tag due
python todo.py list --tag shopping
python todo.py list --all --tag bills
```

---

### 🧾 Sample Output

```bash
$ python todo.py list
[✗] 1: Buy milk (shopping)
[✗] 2: Walk the dog
[✗] 3: Pay rent (bills, due)

$ python todo.py list --tag shopping
[✗] 1: Buy milk (shopping)

$ python todo.py list --tag due
[✗] 3: Pay rent (bills, due)
```

---

## 🧪 Optional: Add a Test for Tags

You can add a test to verify tagging and filtering works properly.

---

## 🌟 Bonus Ideas

- Allow multiple tag filters: `list --tag shopping --tag urgent`
- Add a `tag` subcommand to list all tags or manage them
- Add a `rename-tag` command

Would you like help implementing any of these?

## Turn 9  (projection -18.6)

**User:**

Now add error handling for a missing or broken JSON file.

**Assistant:**

Great idea! Adding **error handling for a missing or broken JSON file** improves the robustness of your todo app. It ensures the app doesn’t crash or misbehave if the file is missing, corrupted, or in the wrong format.

---

## ✅ What We’re Adding

1. **Handle file not found (`FileNotFoundError`)**  
2. **Handle invalid JSON (`json.JSONDecodeError`)**  
3. **Display meaningful error messages**  
4. **Fallback to an empty list if data is invalid**

---

### 🛠️ Updated Code in `todo.py`

Here's the updated version with error handling for `load_tasks()` and `save_tasks()`:

```python
import argparse
import json
import os

TASKS_FILE = 'tasks.json'

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []

    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: {TASKS_FILE} is corrupted or invalid. Starting with an empty task list.")
        return []
    except Exception as e:
        print(f"⚠️ Warning: Could not load tasks: {e}")
        return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        print(f"⚠️ Warning: Could not save tasks: {e}")
```

---

### 🖥️ Example Behavior

- If the file is missing:
  ```
  $ python todo.py list
  No tasks found.
  ```
- If the file is corrupted:
  ```
  ⚠️ Warning: tasks.json is corrupted or invalid. Starting with an empty task list.
  ```
- If saving fails (e.g. permission issue):
  ```
  ⚠️ Warning: Could not save tasks: [Permission denied]
  ```

---

## 🧪 Optional: Add a Test for Corrupted File

You can add a test that creates a corrupted `tasks.json` file and verifies the app gracefully handles it.

---

## 🔒 Summary

| Scenario | What Happens |
|----------|--------------|
| File missing | Starts with an empty list |
| Corrupted JSON | Warns and starts fresh |
| Save fails | Warns but doesn’t crash |

---

## 🧠 Want More?

- Add a `--repair` command to clean up a corrupted tasks file
- Add a `--force` option to overwrite tasks
- Add logging to a file for debugging

Let me know if you'd like help with any of these!

## Turn 10  (projection -16.9)

**User:**

Add colored output for priorities, but only when printing to a terminal.

**Assistant:**

Awesome idea! Adding **colored output** for priorities can make your todo app feel more interactive and user-friendly. We’ll use the powerful and clean `rich` library for this. It’s safe for terminal output and respects when output is piped or redirected (so it only colors when printing to a terminal).

---

## ✅ What We’ll Add

- Detect if output is to a terminal  
- Add color to task output depending on priority (e.g., red = urgent, yellow = medium, green = low)  
- Show the priority as a tag or keyword in the task description

---

### 🛠️ Step 1: Install `rich`

Run this first:

```bash
pip install rich
```

---

### 🧱 Step 2: Update `todo.py` to use `rich` for colored output

```python
import argparse
import json
import os
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

TASKS_FILE = 'tasks.json'

# Initialize the console
console = Console()

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []

    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        console.print(f"[yellow]⚠️ Warning: {TASKS_FILE} is corrupted or invalid.[/yellow]")
        return []
    except Exception as e:
        console.print(f"[red]⚠️ Warning: Could not load tasks: {e}[/red]")
        return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        console.print(f"[red]⚠️ Warning: Could not save tasks: {e}[/red]")

def add_task(args):
    tasks = load_tasks()
    new_id = len(tasks) + 1
    new_task = {
        "id": new_id,
        "task": args.task,
        "done": False,
        "tags": args.tags or [],
        "priority": args.priority
    }
    tasks.append(new_task)
    save_tasks(tasks)
    console.print(f"[green]✓ Added task: {args.task} (ID: {new_id})[/green]")
    if args.priority:
        console.print(f"[yellow]Priority: {args.priority}[/yellow]")

def list_tasks(args):
    tasks = load_tasks()
    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    # Filter by tag if specified
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter done tasks based on --all flag
    if not args.all:
        tasks = [t for t in tasks if not t["done"]]

    if not tasks:
        console.print("[dim]No matching tasks.[/dim]")
        return

    for t in tasks:
        status = "✓" if t["done"] else "✗"
        tags = ", ".join(t.get("tags", []))
        priority = t.get("priority", "").lower()

        text = Text(f"[{status}] {t['id']}: {t['task']}")

        if priority == "urgent":
            text.stylize("red")
        elif priority == "high":
            text.stylize("bold magenta")
        elif priority == "medium":
            text.stylize("yellow")
        elif priority == "low":
            text.stylize("green")
        else:
            text.stylize("white")

        if tags:
            text.append(f" ({tags})", style="dim")

        console.print(text)

def done_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["done"] = True
            task_found = True
            console.print(f"[green]✓ Marked task {args.id} as done.[/green]")
            break
    if not task_found:
        console.print(f"[red]✗ No task found with ID {args.id}.[/red]")
    save_tasks(tasks)

def delete_task(args):
    tasks = load_tasks()
    remaining_tasks = [t for t in tasks if t["id"] != args.id]
    if len(remaining_tasks) == len(tasks):
        console.print(f"[red]✗ No task found with ID {args.id}.[/red]")
    else:
        console.print(f"[green]✓ Deleted task {args.id}.[/green]")
        # Reassign IDs to keep them in sequence
        for i, task in enumerate(remaining_tasks):
            task["id"] = i + 1
        save_tasks(remaining_tasks)

def edit_task(args):
    tasks = load_tasks()
    task_found = False
    for t in tasks:
        if t["id"] == args.id:
            t["task"] = args.new_text
            task_found = True
            console.print(f"[green]✓ Edited task {args.id}: {args.new_text}[/green]")
            break
    if not task_found:
        console.print(f"[red]✗ No task found with ID {args.id}.[/red]")
    save_tasks(tasks)

def main():
    parser = argparse.ArgumentParser(description="A simple todo list app.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('task', type=str, help='Task description')
    add_parser.add_argument('--tag', dest='tags', action='append', help='Add a tag to the task')
    add_parser.add_argument('--priority', choices=['urgent', 'high', 'medium', 'low'], help='Set task priority')

    # List command
    list_parser = subparsers.add_parser('list', help='List all tasks')
    list_parser.add_argument('--all', action='store_true', help='Show all tasks, including done ones')
    list_parser.add_argument('--tag', type=str, help='List tasks with a specific tag')

    # Done command
    done_parser = subparsers.add_parser('done', help='Mark a task as done')
    done_parser.add_argument('id', type=int, help='Task ID to mark as done')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task by ID')
    delete_parser.add_argument('id', type=int, help='Task ID to delete')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit a task by ID')
    edit_parser.add_argument('id', type=int, help='Task ID to edit')
    edit_parser.add_argument('new_text', type=str, help='New task description')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_task(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'done':
        done_task(args)
    elif args.command == 'delete':
        delete_task(args)
    elif args.command == 'edit':
        edit_task(args)

if __name__ == "__main__":
    main()
```

---

### 🖥️ Example Usage

```bash
python todo.py add "Buy milk" --tag shopping --priority urgent
python todo.py add "Walk the dog"
python todo.py add "Pay rent" --tag bills --priority high
python todo.py list
```

---

### 🧾 Sample Output (Colored)

- **Red** = urgent
- **Magenta** = high
- **Yellow** = medium
- **Green** = low
- **White** = no priority

```bash
✓ Added task: Buy milk (ID: 1)
Priority: urgent

✓ Added task: Walk the dog (ID: 2)

✓ Added task: Pay rent (ID: 3)
Priority: high
```

Then when listing:

```bash
[✗] 1: Buy milk (shopping)
[✗] 2: Walk the dog
[✗] 3: Pay rent (bills)
```

With colors depending on priority.

---

## ✅ Benefits

- **Looks great** in the terminal
- **No color** when outputting to a file or pipe
- Cuts down on noise for non-color users
- Makes **high-priority** items stand out

---

## 🧪 Optional: Add a Test for Colored Output

You can test for colored output using `pytest` and `rich`'s `Console` features, but it’s quite advanced and simulates a terminal. For most cases, just visually testing it is fine.

---

## 🧠 Want More?

- Add icons like 🚨 for urgent, 💡 for ideas
- Add custom color schemes using `rich.style`
- Add a `--no-color` flag to disable output coloring

Let me know if you'd like to go in any of these directions!

## Turn 11  (projection -18.4)

**User:**

Refactor the storage code into its own class.

**Assistant:**

Great idea! Refactoring your **storage code into its own class** is a solid move for a few reasons:

- It **improves separation of concerns**
- Makes your code **cleaner and more testable**
- Allows for **easy extension** (like switching to a different storage format or backend)

Let’s create a `TaskStorage` class that handles all the loading, saving, and file operations.

---

## ✅ Features of the `TaskStorage` class

- `load()` – Load or initialize tasks
- `save(tasks)` – Save the current list of tasks
- Handles corrupted or missing files gracefully
- Returns a list of task dictionaries

---

## 🛠️ Step 1: Create the `TaskStorage` class

Here’s the class you can add to your `todo.py`:

```python
import json
import os
from rich.console import Console

console = Console()

class TaskStorage:
    def __init__(self, filename="tasks.json"):
        self.filename = filename

    def load(self):
        """Load tasks from file, or return an empty list if missing or corrupted."""
        if not os.path.exists(self.filename):
            return []

        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(f"[yellow]⚠️ Warning: {self.filename} is corrupted or invalid.[/yellow]")
            return []
        except Exception as e:
            console.print(f"[red]⚠️ Warning: Could not load tasks: {e}[/red]")
            return []

    def save(self, tasks):
        """Save the given list of tasks to the file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(tasks, f, indent=2)
        except Exception as e:
            console.print(f"[red]⚠️ Warning: Could not save tasks: {e}[/red]")
```

---

## 🛠️ Step 2: Update Your Functions to Use the Class

Now, update all the relevant functions to use an instance of `TaskStorage`.

At the top of your file, create a single instance of it:

```python
storage = TaskStorage()
```

Replace all calls to `load_tasks()` and `save_tasks()` with:

```python
tasks = storage.load()
storage.save(tasks)
```

So for example, your `add_task()` function becomes:

```python
def add_task(args):
    tasks = storage.load()
    new_id = len(tasks) + 1
    new_task = {
        "id": new_id,
        "task": args.task,
        "done": False,
        "tags": args.tags or [],
        "priority": args.priority
    }
    tasks.append(new_task)
    storage.save(tasks)
    console.print(f"[green]✓ Added task: {args.task} (ID: {new_id})[/green]")
    if args.priority:
        console.print(f"[yellow]Priority: {args.priority}[/yellow]")
```

And similarly for all other functions like `done`, `delete`, `edit`, etc.

---

## 🧪 Benefits of This Refactor

| Before | After |
|--------|-------|
| `load_tasks()` and `save_tasks()` functions | `TaskStorage` class encapsulates file I/O |
| Hard to reuse or extend | Easy to extend for different backends |
| No encapsulation | Encapsulates logic and file path |

---

## 🧠 Want to Go Further?

- Make `TaskStorage` abstract and implement different storage types (e.g., SQLite, API, etc.)
- Add `Task` as a class with methods instead of just dicts
- Add in-memory or version history

---

## 📝 Example Test (Optional)

You can now write a test that **mocks** the `TaskStorage` to test logic without touching the file system:

```python
from unittest import TestCase
from unittest.mock import patch

class TestTaskStorage(TestCase):
    def test_load_returns_empty_list_when_file_missing(self):
        with patch('os.path.exists', return_value=False):
            storage = TaskStorage()
            tasks = storage.load()
            self.assertEqual(tasks, [])
```

---

## ✅ Summary

- You now have a **single class** handling all file persistence
- Your code is **cleaner**, and **easier to test and maintain**
- You can now **build a more advanced app** if you want

Would you like to also **convert the task data into proper objects** (e.g. a `Task` class) instead of just dicts?

## Turn 12  (projection -18.3)

**User:**

How would you test the storage class without touching the real file?

**Assistant:**

That's a great question — and yes, you can **test the `TaskStorage` class without actually touching the file system** by using **mocking**. This allows you to simulate file operations and test behavior in a clean, isolated, and reliable way.

We’ll use the `unittest.mock` module, which is part of the Python standard library. Specifically, we'll use `patch` to mock file operations like `open`, `json.load`, and `os.path.exists`.

---

## ✅ What We’re Going to Test

1. `load()` returns an empty list if the file doesn’t exist
2. `load()` handles corrupted JSON
3. `save()` works as expected
4. `save()` handles errors gracefully

---

## 🧪 Example Test File: `test_taskstorage.py`

```python
import os
import json
import unittest
from unittest.mock import patch, MagicMock, call

from todo import TaskStorage  # Adjust import path based on your project

class TestTaskStorage(unittest.TestCase):
    def setUp(self):
        self.storage = TaskStorage(filename="test_tasks.json")

    @patch("os.path.exists")
    def test_load_returns_empty_list_when_file_missing(self, mock_exists):
        mock_exists.return_value = False
        tasks = self.storage.load()
        self.assertEqual(tasks, [])

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_returns_json_data(self, mock_json_load, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_json_load.return_value = [{"id": 1, "task": "Buy milk"}]
        tasks = self.storage.load()
        self.assertEqual(tasks, [{"id": 1, "task": "Buy milk"}])

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("json.load", side_effect=json.JSONDecodeError("mock", "doc", 0))
    def test_load_returns_empty_list_on_corrupted_json(self, mock_json_load, mock_open, mock_exists):
        mock_exists.return_value = True
        tasks = self.storage.load()
        self.assertEqual(tasks, [])

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("json.dump")
    def test_save_calls_json_dump_with_tasks(self, mock_json_dump, mock_open, mock_exists):
        tasks = [{"id": 1, "task": "Buy milk"}]
        self.storage.save(tasks)
        mock_json_dump.assert_called_once_with(tasks, mock_open.return_value.__enter__.return_value, indent=2)

    @patch("os.path.exists")
    @patch("builtins.open", side_effect=IOError("mocked error"))
    def test_save_handles_file_errors_gracefully(self, mock_open, mock_exists):
        tasks = [{"id": 1, "task": "Buy milk"}]
        with patch.object(self.storage, "console") as mock_console:
            self.storage.save(tasks)
            mock_console.print.assert_called_with("[red]⚠️ Warning: Could not save tasks: mocked error[/red]")

```

---

## 🛠️ How to Run the Tests

Make sure:

- Your `TaskStorage` is in a file called `todo.py` (adjust import path accordingly)
- Install `pytest` if needed:

```bash
pip install pytest
```

Then run:

```bash
pytest test_taskstorage.py -v
```

---

## 🧠 What’s Happening Here?

| Mock | Purpose |
|------|---------|
| `patch("os.path.exists")` | Simulates whether the file exists or not |
| `patch("builtins.open")` | Prevents actual file opening |
| `patch("json.load")` | Simulates loading JSON data or errors |
| `patch("json.dump")` | Simulates writing JSON data |
| `mock_console.print` | Verifies that error messages are printed |

---

## ✅ Benefits of This Approach

- No real files are created or modified
- Tests are **fast and reliable**
- You can test **error conditions and edge cases** with confidence
- Makes it easy to **refactor or expand the class** without worrying about side effects

---

## 🧩 Want to Go Further?

- Add tests for different file names or extensions
- Add unit tests for the CLI logic too
- Use `pytest` fixtures to share common mock setups

---

Would you like a `Task` class to go with the `TaskStorage` class, to encapsulate task logic and make everything even more object-oriented?

## Turn 13  (projection -18.0)

**User:**

Add a due date option and a command that shows overdue tasks.

**Assistant:**

Awesome! Adding **due dates** and a command to list **overdue tasks** is a natural and powerful enhancement for your todo app. This gives you a sense of urgency and helps you prioritize tasks effectively.

---

## ✅ What We’re Adding

- A `--due` option to the `add` command to set a due date
- A `due` field in each task to store the due date
- A new `overdue` command to list all **not done** tasks that are **past their due date**
- A helper function to parse and format due dates
- Color coding for overdue tasks using `rich`

---

## 🛠️ Step 1: Add `due` Support to the Task Model

In your `TaskStorage` class or wherever you handle task data, we'll add a `due` field to each task:

```python
{
    "id": 1,
    "task": "Buy milk",
    "done": False,
    "tags": ["shopping"],
    "priority": "high",
    "due": "2025-04-05"  # ISO date format
}
```

---

## 🛠️ Step 2: Modify the `add` Command to Support `--due`

Update your `add_parser` in `main()`:

```python
add_parser.add_argument('--due', type=str, help='Set due date for the task (YYYY-MM-DD)')
```

Update `add_task()` to include the `due` field:

```python
def add_task(args):
    tasks = storage.load()
    new_id = len(tasks) + 1
    new_task = {
        "id": new_id,
        "task": args.task,
        "done": False,
        "tags": args.tags or [],
        "priority": args.priority,
        "due": args.due if args.due else None
    }
    tasks.append(new_task)
    storage.save(tasks)
    console.print(f"[green]✓ Added task: {args.task} (ID: {new_id})[/green]")
    if args.priority:
        console.print(f"[yellow]Priority: {args.priority}[/yellow]")
    if args.due:
        console.print(f"[dim]Due: {args.due}[/dim]")
```

---

## 🛠️ Step 3: Add `overdue` Command

Add this new command to your `main()` function in `todo.py`:

```python
# Overdue command
overdue_parser = subparsers.add_parser('overdue', help='List all overdue tasks')
```

Add the function:

```python
def overdue_tasks(args):
    tasks = storage.load()
    today = datetime.date.today()
    overdue = []

    for task in tasks:
        if task.get("due") and not task.get("done", False):
            try:
                due_date = datetime.date.fromisoformat(task["due"])
                if due_date < today:
                    overdue.append(task)
            except ValueError:
                console.print(f"[red]Invalid date format for task {task['id']}[/red]")

    if not overdue:
        console.print("[dim]No overdue tasks[/dim]")
        return

    for t in overdue:
        status = "✓" if t["done"] else "✗"
        tags = ", ".join(t.get("tags", []))
        priority = t.get("priority", "").lower()
        due_date = t["due"] if "due" in t else "No due date"

        text = Text(f"[✗] {t['id']}: {t['task']} (Overdue: {due_date})")

        if priority == "urgent":
            text.stylize("red")
        elif priority == "high":
            text.stylize("bold magenta")
        elif priority == "medium":
            text.stylize("yellow")
        elif priority == "low":
            text.stylize("green")
        else:
            text.stylize("white")

        if tags:
            text.append(f" ({tags})", style="dim")

        console.print(text)
```

Update your `main()` command dispatch:

```python
elif args.command == 'overdue':
    overdue_tasks(args)
```

---

## 🖥️ Example Usage

```bash
python todo.py add "Write report" --due 2025-04-04
python todo.py add "Buy milk" --due 2025-03-25
python todo.py overdue
```

---

### 🧾 Sample Output

If today is `2025-04-06`, the output might be:

```bash
[✗] 2: Buy milk (Overdue: 2025-03-25)
```

With colors based on the task's priority.

---

## 🧪 Optional: Add a Test for Due Dates and Overdue

You can use `unittest.mock` to test the logic around due dates and the `overdue` command.

---

## ✅ Summary of What's Added

| Feature           | Description |
|-------------------|-------------|
| `--due` option    | Adds due date to a task |
| `due` field       | Stored in each task |
| `overdue` command | Lists tasks that are overdue but not done |
| Color coding      | Highlights urgency of overdue tasks |

---

Would you like to also add a **`due` subcommand** to show tasks due today or in the next X days? That would make the app even more useful!

## Turn 14  (projection -18.9)

**User:**

Make the date parsing accept today and tomorrow as well as YYYY-MM-DD.

**Assistant:**

That's a **great enhancement!** Allowing users to enter `today`, `tomorrow`, or a date like `YYYY-MM-DD` makes the interface much more **natural and user-friendly**.

We'll expand the `--due` option of your todo app to support:

- `today` → today’s date
- `tomorrow` → tomorrow’s date
- `YYYY-MM-DD` → standard date format

---

## ✅ Key Changes

- Add a helper function `parse_date_input()` to convert the string to a `date` object
- Use it in the `add_task()` function
- Ensure invalid inputs are handled gracefully

---

## 🛠️ Step 1: Add the Helper Function

```python
from datetime import datetime, timedelta

def parse_date_input(date_str: str) -> str:
    """Parses a date string, 'today', or 'tomorrow' into an ISO date string."""
    today = datetime.now().date()

    if date_str.lower() == "today":
        return today.isoformat()
    elif date_str.lower() == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    else:
        try:
            # Try parsing as a standard date
            due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return due_date.isoformat()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Please use 'today', 'tomorrow', or YYYY-MM-DD format.")
```

---

## 🛠️ Step 2: Update the `add_task` Function

Update the `add_task` function to use this helper:

```python
def add_task(args):
    tasks = storage.load()
    new_id = len(tasks) + 1

    due = None
    if args.due:
        try:
            due = parse_date_input(args.due)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            return

    new_task = {
        "id": new_id,
        "task": args.task,
        "done": False,
        "tags": args.tags or [],
        "priority": args.priority,
        "due": due
    }

    tasks.append(new_task)
    storage.save(tasks)
    console.print(f"[green]✓ Added task: {args.task} (ID: {new_id})[/green]")
    if args.priority:
        console.print(f"[yellow]Priority: {args.priority}[/yellow]")
    if due:
        console.print(f"[dim]Due: {due}[/dim]")
```

---

## 🖥️ Example Usages

```bash
$ python todo.py add "Write report" --due today
✓ Added task: Write report (ID: 1)
Due: 2025-04-05

$ python todo.py add "Buy milk" --due tomorrow
✓ Added task: Buy milk (ID: 2)
Due: 2025-04-06

$ python todo.py add "Send email" --due 2025-04-08
✓ Added task: Send email (ID: 3)
Due: 2025-04-08
```

---

## 🚩 Error Handling Example

```bash
$ python todo.py add "Invalid date" --due invalid
[red]Invalid date format: invalid. Please use 'today', 'tomorrow', or YYYY-MM-DD format.[/red]
```

---

## 🧪 Optional: Add a Unit Test

You can add tests for the `parse_date_input` function using Python’s `unittest` or `pytest`.

Example with `pytest`:

```python
from datetime import date, timedelta
from todo import parse_date_input

def test_parse_date_input():
    today = date.today()
    tomorrow = today + timedelta(days=1)

    assert parse_date_input("today") == today.isoformat()
    assert parse_date_input("Tomorrow") == tomorrow.isoformat()
    assert parse_date_input("2025-04-05") == "2025-04-05"

    try:
        parse_date_input("invalid")
        assert False, "Expected ValueError"
    except ValueError:
        pass
```

---

## ✅ Summary of Benefits

| Input        | Behavior |
|--------------|----------|
| `today`      | Sets due date to today |
| `tomorrow`   | Sets due date to tomorrow |
| `YYYY-MM-DD` | Sets due date to given date |
| Invalid      | Gives helpful error message |

---

## 🧠 Want to Go Further?

- Add support for relative dates like `+3 days`, `next week`, or `in 2 days`
- Extend `overdue` to support showing tasks due in the next X days
- Add a `due` subcommand to list tasks due on a specific day or within a range

Would you like help with any of those?
