from fastapi import FastAPI, UploadFile, Form, File
import os, io
from PIL import Image
from compreface import CompreFace
from compreface.service import VerificationService
from collections import OrderedDict
from fastapi.middleware.cors import CORSMiddleware
import base64


def save_image(mobile_number, child_no, image):
    base_folder = "signup"
    
    image_filename = f"{mobile_number}_{child_no}.jpg"
    image_path = os.path.join(base_folder, image_filename)
    
    with open(image_path, "wb") as img_file:
        img_file.write(image.file.read())

        
def perform_verification(image_path1: str, image_path2: str, domain: str, port: int, verification_api_key: str) -> float:
    compre_face = CompreFace(domain, port, {
        "limit": 0,
        "det_prob_threshold": 0.8,
        "face_plugins": "age,gender",
        "status": "true",
        
    })
    print("paths",image_path1, image_path2)
    verify = compre_face.init_face_verification(verification_api_key)

    data = verify.verify(image_path1, image_path2)
    # print(data)
    # print(data)
    # print(type(data))
    if "message" in data.keys():
        return False

    # if data['message']=='No face is found in the given image':
    #     return False

    #{'message': 'No face is found in the given image', 'code': 28}
    print("_______________________________________________________________________-", data)
    similarity = data['result'][0]['face_matches'][0]['similarity']
    print(similarity)
    return similarity



def get_images_from_folders(main_folder: str) -> list:
    file_paths = []
    base_folder= "signup"
    
    for filename in os.listdir(base_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(base_folder, filename)
            file_paths.append(file_path)
    
    print(file_paths)
    return file_paths



def base64_to_jpg(base64_string, output_path):
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    image.save(output_path, format="JPEG")
    return output_path

def signin(image_path, path):
    DOMAIN: str = 'http://localhost'
    PORT: str = '8009'
    VERIFICATION_API_KEY: str = 'b925454d-8651-48f4-ba98-768ac98f8e21'
    get_images= get_images_from_folders(path)
    similarity= []
    for i in get_images:
        similar= perform_verification(i, image_path, DOMAIN, PORT, VERIFICATION_API_KEY)
        if similar!= False and similar>0.97:
            temp=[]
            temp.append(i)
            temp.append(similar)
            similarity.append(temp)
        else:
            print("hello",similar, i)
    if len(similarity)>0:
        similarity = sorted(similarity, key=lambda x: x[1])
        print(similarity[-1])

        print("fewffef")
        mob= similarity[-1][0][7:].split("_")[0]
        print("mob is ,", mob)
        child= similarity[-1][0][7:].split("_")[1][:1]
        print(similarity)   

        return OrderedDict({"success": True, "mob": mob, "child": child})

    else:
        return OrderedDict({"success": False})


signin("nospecs.jpg", "signup/")



def save_image_to_temp(image):
    temp_folder = "temp_images"
    os.makedirs(temp_folder, exist_ok=True)
    image_path = os.path.join(temp_folder, image.filename)
    with open(image_path, "wb") as img_file:
        img_file.write(image.file.read())
    return image_path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/signup/")
async def signup(
    mobile_number: str = Form(...),
    child_no: str = Form(...),
    image: str = Form(...)
):
    base_folder = "signup"
    
    filename= f"{mobile_number}_{child_no}.jpg"
    image_path = os.path.join(base_folder, filename)
    base64_to_jpg(image, image_path)
    print("successful")
    return {"message": "Signup successful"}

    
@app.post("/signin/")
async def face_signin(image: str = Form(...)):

    image_path = base64_to_jpg(image, "temp/temp.jpg")
    # print(image_path)
    result= signin(image_path, "signup")
    print(result)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
