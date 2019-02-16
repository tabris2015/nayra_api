from app import app, db
from app.models import Word, Action


actions_list = [
    ['traction', 'adelante'],
    ['led', 'blink'],
    ['traction', ' atras'],
    ['greet', 'hola'],
    ['greet', 'adios']
]

with open("es-ES/pronounciation-dictionary.dict", "r") as f:
    content = f.read().split("\n")

words = [x.split(" ")[0] for x in content]

i = 0
for word in words:
    w = Word(word=word)
    db.session.add(w)
    i += 1

for action in actions_list:
    a = Action(category=action[0], action=action[1])
    db.session.add(a)



db.session.commit()
print("insertadas {} palabras".format(i))