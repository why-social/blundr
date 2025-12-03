import pandas as pd

def aggregate_files(user_1: dict, user_2: dict):
    return f"User_1_face: {user_1["face"]}\nUser_1_voice: {user_1["voice"]}\nUser_2_face: {user_2["face"]}\nUser_2_voice: {user_2["voice"]}"
