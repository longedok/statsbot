import json


def make_keyboard(buttons, columns=2):
    keyboard, row = [], []
    for i, button in enumerate(buttons):
        row.append({
            "text": button[0],
            "callback_data": json.dumps(button[1])
        })

        if i % columns == 1:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return keyboard

