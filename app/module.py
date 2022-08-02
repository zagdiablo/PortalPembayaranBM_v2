import os


def get_absolute_path(folder):
    return os.path.abspath(f'./{folder}')


def format_name(name_part):
    splited_name = [letter for letter in name_part]
    splited_name[0] = splited_name[0].upper()
    return ''.join(splited_name)