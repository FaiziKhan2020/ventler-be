import json
from fastapi import (Body, Depends, FastAPI, HTTPException,
                     Request)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated
from dotenv import dotenv_values
from supabase import Client, create_client
from articles import fetchArtcile
from openai_rewrite import gpt_rewrite

#Supabase Configuration
config = dotenv_values(".env")
url = "https://tsmvewvgfvsbvuwblfkm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzbXZld3ZnZnZzYnZ1d2JsZmttIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY4ODgxNjgyNCwiZXhwIjoyMDA0MzkyODI0fQ.nVtHkVdbjRVUFRENTzx96-W9BJlBgKk7acuDPXrjEqc"
supa: Client = create_client(url, key)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ventler-fe.vercel.app","http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def helloWorld():
    return "App is running!"

@app.post("/login")
def userLogin(request: Annotated[dict, Body()]):
    try:
        print(key)
        print(url)
        res = supa.auth.sign_in_with_password({"email":request["email"], "password": request["password"]})
    except:
        return {"error": "Invalid Login Credentials"}
    return {"access_token": res.session.access_token}

@app.post("/me")
def getMe(request: Annotated[dict, Body()]):
    token = request["token"]
    res = supa.auth.get_user(token)
    return res.user.email

@app.post("/generate")
async def generateContent(request: Annotated[dict, Body()]):
    url = request["url"]
    if url:
        article = fetchArtcile(url)
        print(f"\nArticle HTML: {article.doc} {article.article_html}")
        rewrite = await gpt_rewrite(article.title,article.text, article.summary)
        return {"content": rewrite}
    else:
        return {"content": ""}