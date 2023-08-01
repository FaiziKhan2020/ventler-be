import json
import os
import asyncio
from fastapi import (Body, Depends, FastAPI, HTTPException,
                     Request)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated
# from dotenv import dotenv_values
from supabase import Client, create_client
from articles import fetchArtcile
from openai_rewrite import gpt_rewrite
from asyncio import Semaphore
from wordpress import upload_to_wordpress

#Supabase Configuration
# config = dotenv_values(".env")
url = os.getenv("SUPABASE_PROJECT_URL","")
key = os.getenv("SUPABASE_SECRET_KEY","")
stable_diff_key = os.getenv("STABLE_DIFFUSION_KEY","")
openai_key = os.getenv("OPEN_AI_KEY","")
supa: Client = create_client(url, key)

semaphore = Semaphore(1)
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
        rewrite = await gpt_rewrite(article.title,article.text, article.summary, openai_key)
        return {"content": rewrite}
    else:
        return {"content": ""}

@app.post("/add_wpress")
async def addWordpressSite(request: Annotated[dict, Body()]):
    siteName = request['title']
    url = request['url']
    user = request['user']
    creds = request['creds']
    inputPrompt = request['prompt']
    categories = request['categories']
    # add in to the supabase table
    try:
        supa.table("config").insert({
            "credential_name": "wordpress",
            "credential_value": creds,
            "wordpress_site": siteName,
            "wordpress_url": url,
            "user_prompt": inputPrompt,
            "wordpress_user": user,
            "categories": categories,
            "user_id": "65da9556-ecb2-4f9c-8553-db66d6159ccb"
        }).execute()
        return {"message": "Record created successfully!"}
    except err:
        return err
    
@app.post("/update_wpress")
async def updateWordpressSite(request: Annotated[dict, Body()]):
    id = request['id']
    siteName = request['title']
    url = request['url']
    user = request['user']
    creds = request['creds']
    inputPrompt = request['prompt']
    categories = request['categories']
    # add in to the supabase table
    try:
        supa.table("config").update({
            "credential_name": "wordpress",
            "credential_value": creds,
            "wordpress_site": siteName,
            "wordpress_url": url,
            "user_prompt": inputPrompt,
            "wordpress_user": user,
            "categories": categories,
            "user_id": "65da9556-ecb2-4f9c-8553-db66d6159ccb"
        }).eq("id",id).execute()
        return {"message": "Record created successfully!"}
    except err:
        return err
@app.post("/delete_wpress")
async def deleteWordpressSite(request: Annotated[dict, Body()]):
    id = request['id']
    # add in to the supabase table
    try:
        config = supa.table("config").select("*").eq("id",id).execute()
        supa.table("config").delete("*").eq("id",id).execute()
        supa.table("process").delete("*").eq("wordpress_url",config.data[0]['wordpress_url']).execute()
        return {"message": "Record deleted successfully!"}
    except err:
        return err
    
@app.post("/prompt_settings")
async def promptSettings(request: Annotated[dict, Body()]):
    base_prompt = request['base_prompt']
    body_prompt = request['body_prompt']
    title_prompt = request['title_prompt']
    slug_prompt = request['slug_prompt']
    headings_prompt = request['headings_prompt']
    conclusion_prompt = request['conclusion_prompt']
    total_headings = request['total_headings']
    default_language = request['default_language']
    default_tone = request['default_tone']
    length = request['length']
    # add in to the supabase table
    try:
        supa.table("config").update({
            "credential_name": "prompt_settings",
            "base_prompt" : base_prompt,
            "title_prompt" : title_prompt,
            "slug_prompt" : slug_prompt,
            "headings_prompt" : headings_prompt,
            "conclusion_prompt" : conclusion_prompt,
            "total_headings" : total_headings,
            "default_language" : default_language,
            "tone" : default_tone,
            "length" : length,
            "body_prompt" : body_prompt,
            "user_id": "65da9556-ecb2-4f9c-8553-db66d6159ccb"
        }).eq("credential_name","prompt_settings").execute()
        return {"message": "Record created successfully!"}
    except err:
        return err
    

@app.post("/openai_creds")
async def setOpenAiCreds(request: Annotated[dict, Body()]):
    creds = request["openai_creds"]
    try:
        supa.table("config").upsert({
            "credential_name": "open_ai",
            "credential_value": creds,
            "wordpress_site": "",
            "wordpress_url": "",
            "user_prompt": "",
            "user_id": "65da9556-ecb2-4f9c-8553-db66d6159ccb"
        }).execute()
        return {"message": "Record created successfully!"}
    except err:
        return err
    
@app.get("/configs")
async def getConfigs():
    try:
        data = supa.table("config").select("*").eq("user_id","65da9556-ecb2-4f9c-8553-db66d6159ccb").execute()
        return {"configs": data }
    except err:
        return err
    
@app.post("/insert_queue")
async def insertToQueue(request: Annotated[dict, Body()]):
    title = request["title"] if request["title"] is not None else ""
    url = request["url"] if request["url"] is not None else "" 
    wordpress_url = request["wordpress_url"] if request["wordpress_url"] is not None else "" 
    site = request["site"] if request["site"] is not None else "" 
    length = request["length"] if request["length"] is not None else None 
    tone = request["tone"] if request["tone"] is not None else None
    language = request["language"] if request["language"] is not None else None
    headings = request["headings"] if request["headings"] is not None else None
    main_prompt = request["main_prompt"] if request["main_prompt"] is not None else ""
    auto_upload = request["auto_upload"] if request["auto_upload"] is not None else True 
    author = None if request["author"] is None else request["author"]
    category = None if request["category"] is None else request["category"]
    try:
        supa.table("process").insert({
            "title": title,
            "article_url": url,
            "wordpress_url": wordpress_url,
            "wordpress_site": site,
            "user_id": "65da9556-ecb2-4f9c-8553-db66d6159ccb",
            "status": "In Queue",
            "length" : length,
            "tone" : tone,
            "language" : language,
            "headings" : headings,
            "main_prompt" : main_prompt,
            "auto_upload" : auto_upload,
            "author": author,
            "category": category,
        }).execute()
        supa.table("config").update({
                "user_prompt": main_prompt,
                "default_category": category,
                "auto_upload": auto_upload,
                "length" : length,
                "tone" : tone,
                "default_language" : language,
                "total_headings" : headings,
                "author": author,
            }).eq("wordpress_url",wordpress_url).execute()
    except Exception as err:
        return err
@app.post("/regen")
async def regenerate(request: Annotated[dict, Body()]):
    id = request["item_id"]
    try:
        supa.table("process").update({
                "status": "In Queue",
                "error": ""
            }).eq("id",id).execute()
        return {"status": "Regeneration started!"}
    except Exception as err:
        return err
@app.post("/upload")
async def uploadToWp(request: Annotated[dict, Body()]):
    id = request["item_id"]
    try:
        data = supa.table("process").select("*").eq("id",id).execute()
        article = data.data[0]
        wp_config_data = supa.table("config").select("*").eq("user_id","65da9556-ecb2-4f9c-8553-db66d6159ccb").eq("wordpress_url",article["wordpress_url"]).execute()
        wp_config = wp_config_data.data
        if len(wp_config) == 0:
            raise Exception("No wordpress URL is present")
        # do the upload
        url = await upload_to_wordpress(article["article_title"],article["output_html"],article["slug"],wp_config[0]["wordpress_url"],wp_config[0]["credential_value"],wp_config[0]["wordpress_user"])
        supa.table("process").update({
            "post_url": url
        }).eq("id",id).execute()
        return {"status": "Regeneration started!"}
    except Exception as err:
        print("in error ", err)
        return err
    
    
@app.get("/get_queue")
async def getQueue():
    try:
        data = supa.table("process").select("*").eq("user_id","65da9556-ecb2-4f9c-8553-db66d6159ccb").execute()
        return {"queue": data}
    except err:
        return 'Error occurred'
    
# Here you create the function do you want to schedule
     
@app.get("/do")
async def process_loop():
    async with semaphore:
        #call the processing here
        await generate_articles()
        asyncio.create_task(process_loop())
        return True
    
async def generate_articles():
    #Fetch In Queue articles
    in_queue_articles = supa.table("process").select("*").eq("user_id","65da9556-ecb2-4f9c-8553-db66d6159ccb").eq("status","In Queue").execute()
    if len(in_queue_articles.data) > 0:
        article = in_queue_articles.data[0]
        try:
            print(f"Article {article}")
            supa.table("process").update({
                "status": "Processing"
                }).eq("id",article["id"]).execute()
            #set the article to processing
            #now first scrape the article url to extract details
            print('111')
            scrapped_article = fetchArtcile(article["article_url"])
            print('222')
            user_configs_data = supa.table("config").select("*").eq("user_id","65da9556-ecb2-4f9c-8553-db66d6159ccb").eq("credential_name","open_ai").execute()
            print('333')
            print(user_configs_data.data[0])
            if user_configs_data.data[0]["credential_value"] is None:
                raise Exception("OpenAI credentials are missing!")
            #now do the magic with open ai to get the final regeneration
            print('444')
            #get the main settings
            main_config_data = supa.table("config").select("*").eq("credential_name","prompt_settings").execute()
            main_config = main_config_data.data[0]
            print("Mcn: ", main_config)
            tone = main_config["tone"] if article["tone"] is None or article["tone"]=="" else article["tone"]
            heads = main_config["total_headings"] if article["headings"] is None or article["headings"] =="" else article["headings"]
            lngth = main_config["length"] if article["length"] is None or article["length"] =="" else article["length"]
            mprompt = None if article["main_prompt"] is None or article["main_prompt"] =="" else article["main_prompt"]
            final_article_data = await gpt_rewrite(scrapped_article.title,scrapped_article.text, scrapped_article.summary, user_configs_data.data[0]["credential_value"],user_configs_data.data[0]["user_prompt"] ,list(scrapped_article.images), stable_diff_key=stable_diff_key, language=article["language"],tone=tone,headings=heads,main_prompt=mprompt,body_prompt=main_config["body_prompt"],title_prompt=main_config["title_prompt"], length=lngth,conclusion_prompt=main_config["conclusion_prompt"],headings_prompt=main_config["headings_prompt"],prd_base_prompt=main_config["base_prompt"],slug_prompt=main_config["slug_prompt"])
            print('555')
            #push the output to supabase
            supa.table("process").update({
                "output_html": final_article_data["article"],
                "slug": final_article_data["slug"],
                "article_title": final_article_data["article_title"]
            }).eq("id",article["id"]).execute()
            wp_config_data = supa.table("config").select("*").eq("user_id","65da9556-ecb2-4f9c-8553-db66d6159ccb").eq("wordpress_url",article["wordpress_url"]).execute()
            print('666')
            if len(wp_config_data.data) == 0:
                raise Exception("No wordpress URL is present")
            print('777')
            wp_config = wp_config_data.data
            print('999 ',article["auto_upload"])
            if article["auto_upload"] == "True" or bool(article["auto_upload"]) is True:
                url = await upload_to_wordpress(final_article_data["title"],final_article_data["article"],final_article_data["slug"],wp_config[0]["wordpress_url"],wp_config[0]["credential_value"],wp_config[0]["wordpress_user"],None if article["author"] is None or article["author"] == "" else article["author"])
                supa.table("process").update({
                "post_url": url
                }).eq("id",article["id"]).execute()
            print('Done!')
            supa.table("process").update({
                "status": "Done"
            }).eq("id",article["id"]).execute()
        except Exception as err:
            error_message = str(err)
            supa.table("process").update({
                "status": "Failed",
                "error": error_message
            }).eq("id",article["id"]).execute()