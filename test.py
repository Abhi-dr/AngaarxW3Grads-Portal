import re

def convert_backticks_to_code(text):
    pattern = r"`(.*?)`"

    result = re.sub(pattern, r"<code>\1</code>", text)
    return result


input_text = input("Enter text: ")
output_text = convert_backticks_to_code(input_text)
print(output_text)

