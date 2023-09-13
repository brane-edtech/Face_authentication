from fastapi import FastAPI, UploadFile, Form, File
import os, io, boto3, pymongo
from PIL import Image
from compreface import CompreFace
from compreface.service import VerificationService
from collections import OrderedDict
from fastapi.middleware.cors import CORSMiddleware
import base64
AWS_BUCKET_NAME = "Your Bucket"
AWS_REGION = "ap-south-1"
AWS_ACCESS_KEY = "Your Access key"
AWS_SECRET_KEY = "Your Secret Key"
base_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/"
AWS_S3_FOLDER = "face_images"

MONGO_CONNECTION_STRING = "Your Mongo string" 
MONGO_DB_NAME = "Your DB" 
MONGO_COLLECTION_NAME = "Your Collection"

client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

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
    print(data)
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
    PORT: str = '8000'
    VERIFICATION_API_KEY: str = 'b925454d-8651-48f4-ba98-768ac98f8e21'

    get_images= get_images_from_folders(path)
    similarity= []
    for i in get_images:
        similar= perform_verification(i, image_path, DOMAIN, PORT, VERIFICATION_API_KEY)
        print(similar)
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
        
        query = {
                    "parentsmobileno": mob
                }

        result = collection.find_one(query)
        data= result['child'][int(child-1)]
        student_name= data['childname']
        
        medium_of_instruction= data["mediumofinstruction"]
        
        grade= data['childclass']
        curriculum= data['childsyllabus']
        

        return OrderedDict({"success": True, "student_name": student_name,
        "medium_of_instruction": medium_of_instruction,
        "grade": grade,
        "curriculum": curriculum
        })

    else:
        return OrderedDict({"success": False})


#signin("nospecs.jpg", "signup/")



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
    mobile_number: str = Form(None),
    child_no: str = Form(None),
    image: str = Form(None)
):
    try:
        base64.b64decode(image)
        base_folder = "signup"
        
        filename= f"{mobile_number}_{child_no}.jpg"
        image_path = os.path.join(base_folder, filename)
        base64_to_jpg(image, image_path)
        print(image_path)
        #path= AWS_S3_FOLDER+image_path
        s3.upload_file(image_path, AWS_BUCKET_NAME, AWS_S3_FOLDER+"/"+image_path[7:])
        print(base_url+AWS_S3_FOLDER+"/"+image_path[7:])
        print("successful")
        return {"message": "Signup successful", "url":base_url+AWS_S3_FOLDER+"/"+image_path[7:]}

    except Exception as e:
        return {"signup":"False", "Error": str(e)}

    
@app.post("/signin/")
async def face_signin(image: str = Form(None)):
 
    try:
        
        base64.b64decode(image)
        print("success")
        image_path = base64_to_jpg(image, "temp/temp.jpg")
        result= signin(image_path, "signup")
        return result


        
        
    except Exception as e:
        return {"signin":"False", "Reason": "Invalid Base64 is sent"}
    # print(image_path)
    # result= signin(image_path, "signup")
    # print(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
