import firebase_admin 
from firebase_admin import credentials, firestore   

cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred) 
db = firestore.client()   

_, ref = db.collection("pruebas").add({"mensaje": "Hola Firestore"}) 
print("Documento creado con ID:", ref.id)   

doc = ref.get() 
print("Contenido:", doc.to_dict()) 