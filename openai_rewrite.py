import openai
import requests
import json
import asyncio
import os

async def gpt_rewrite(title,text,summary, openai_key, user_prompt = None, images = [], stable_diff_key = "", language="English",tone="normal",headings=5,length="very long",main_prompt=None, prd_base_prompt=None,slug_prompt=None,title_prompt=None,conclusion_prompt=None,body_prompt=None,headings_prompt=None, image_prompt=None,heading_image_prompt=None):
    openai.api_key = openai_key
    final_article = ""
    slug = ""
    print('B000')
    # re-write conent
    base_prompt =""
    if prd_base_prompt is not None:
        prd_base_prompt = str(prd_base_prompt).replace("{headings}",headings).replace("{language}",language).replace("{tone}",tone).replace("{length}",length)
        base_prompt = prd_base_prompt
    else:
        base_prompt = f"You should act as a highly professional {language} blog writer, you would be given article text as input and YOU SHOULD using your own knowledge of that domain discussed in the input text write {length} content as detailed as possible in {tone} tone and return correctly formatted html response in {language} language"

    if main_prompt is not None:
        base_prompt = base_prompt + " " + main_prompt
    head_prompt = f"Considering the provided summary of a article please return a stable diffusion prompt that will generate suitable image for blog. Summary: {summary}"
    if heading_image_prompt is not None and heading_image_prompt != "":
        head_prompt = str(heading_image_prompt).replace("{text}",text)
    print('B111')
    chatmessages = [{"role":"system", "content":base_prompt}]
    #get generated article title
    tl_prompt = f"Rewrite the article title {title} in {language} with h1 tag and it should be SEO friendly" if title_prompt is None else str(title_prompt).replace("{context}",title)
    chatmessages.append({"role":"user","content":tl_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    print('B222')
    chatmessages.append(output.choices[0].message)
    final_article = final_article + "<h1>" + str(output.choices[0].message.content).strip('"') + "</h1> </br>"
    print('B333')
    regen_title = output.choices[0].message.content
    regen_title = str(regen_title).strip('"')
    print("B4444")
    #generate main heading image
    chatmessages.append({"role":"user","content":head_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    sd_gen_prompt = output.choices[0].message.content
    print('calling sd: ', sd_gen_prompt)
    image_head = await gen_image_from_prompt(sd_gen_prompt,stable_diff_key)
    print('Imggg: ', image_head)
    if image_head is not None and image_head != "":
        final_article = final_article + f'<img src="{image_head}" /> </br>'
    else: 
        heading_image = ""
        img_prmpt = "Regenrate this image in HQ 4K but it should not look exactly like this" if image_prompt is None else image_prompt
        if len(images) > 0:
            print(images[0])
            heading_image = await gen_image_from_image(img_prmpt, images[0],stable_diff_key)
            print(heading_image)
            final_article = final_article + f'</br> <img src="{heading_image}"/> </br>'
    print("B555 ", headings)
    #get 5 headings considering the article text
    hd_prompt = f"Considering this article text {text} return {headings} sub headings for blog and make sure first one should be an introductory heading and response should be an array which can be parsed through json parsing for example ['Intro heading','heading2','heading3','heading4','heading5']" if headings_prompt is None else f"Considering this article text {text} "+ headings_prompt
    chatmessages.append({"role":"user","content":hd_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    print("B666 ", output.choices[0].message.content)
    #considering it should be returning an array
    sub_headings_arrays = json.loads(output.choices[0].message.content)
    print("B777")
    count = 1
    await asyncio.sleep(60)
    for sub_heads in sub_headings_arrays:
        bdy_prompt = f"For the sub heading {sub_heads} write 3 very long and detailed paragraph in {language} and return response as valid html format" if body_prompt is None else str(body_prompt).replace("{subhead}",sub_heads)
        chatmessages.append({"role":"user","content":bdy_prompt})
        output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
        chatmessages.append(output.choices[0].message)
        final_article = final_article + "<h2>" + sub_heads +"</h2>" +output.choices[0].message.content
        print("B888")
        if len(images) >= count + 1:
            #then there exist image for headings
            img_prmpt = "Regenrate this image in HQ 4K but it should not look exactly like this" if image_prompt is None else image_prompt
            sub_heading_image = await gen_image_from_image(img_prmpt, images[count],stable_diff_key)
            if sub_heading_image is not None:
                final_article = final_article + f'</br> <img src="{sub_heading_image}"/> '
            count=count+1
    #generate conclusion 
    print("B999")
    await asyncio.sleep(60)
    cnc_prompt = f"Check this summary of the article: {summary} write a very long and detailed conclusion paragraph in {language} and return response as valid html format" if conclusion_prompt is None else f"Check this summary of the article: {summary} " + conclusion_prompt
    chatmessages.append({"role":"user","content":cnc_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    final_article = final_article + output.choices[0].message.content
    print("B101010")
    if len(images) > count:
        #then there exist image for conclusion
        sub_heading_image = gen_image_from_image(img_prmpt, images[count],stable_diff_key)
        if sub_heading_image is not None:
            final_article = final_article + f"</br> <img src='{sub_heading_image}'/>"
    print("B11910910")
    slg_prompt = f"For this article create a unique SEO optimized slug as well but return in plain text English with hyphen as separator of words" if slug_prompt is None else slug_prompt
    chatmessages.append({"role":"user","content":slg_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    slug = output.choices[0].message.content
    return {"article": final_article, "title": regen_title, "slug": slug}

async def gen_image_from_image(prompt,image_url,key):
    try:
        print('Url: ', image_url)
        url = "https://stablediffusionapi.com/api/v1/enterprise/img2img"
        payload = json.dumps({
        "key": key,
        "prompt": prompt,
        "model_id": "midjourney",
        "negative_prompt": None,
        "init_image": image_url,
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "guidance_scale": 7.5,
        "strength": 0.7,
        "seed": None,
        "webhook": None,
        "track_id": None
        })
        headers = {
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        print(response.get("output"))
        print(response)
        if len(response.get("output")) !=  0:
             return response.get("output")[0]
        
        if len(response.get("image_links")) != 0:
            return response.get("image_links")[0]
    except Exception as err:
        print(err)
        return ""

async def gen_image_from_prompt(prompt,key):
    try:
        url = "https://stablediffusionapi.com/api/v1/enterprise/text2img"
        payload = json.dumps({
        "key": key,
        "prompt": prompt,
        "model_id": "midjourney",
        "negative_prompt": None,
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "guidance_scale": 7.5,
        "strength": 0.7,
        "seed": None,
        "webhook": None,
        "track_id": None
        })
        headers = {
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        print(response.get("output"))
        if len(response.get("output")) !=  0:
             return response.get("output")[0]
        
        if len(response.get("image_links")) != 0:
            return response.get("image_links")[0]
        
        return None
    except Exception as err:
        print(err)
        return None