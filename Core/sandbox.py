f = open("input.txt", "r")
text = open("text.txt", "r")
dict = []

for line in f:
    dict.append(line.replace("\n", "").lower())

for line in text:
    text1 = line.split(" ")
    for element in text1:
        element = element.replace(",", "").replace(".", "").replace(";", "").replace(" ", "").lower()
        if not element in dict:
            print(element)
