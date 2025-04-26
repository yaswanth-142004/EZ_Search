import json 

with open("dsa.json", "r") as file:
            dsa_data = json.load(file)
            print(len(dsa_data))