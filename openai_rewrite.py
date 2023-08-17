import openai
import requests
import json
import asyncio
import os

async def gpt_rewrite(title,text,summary, openai_key, user_prompt = None, images = [], stable_diff_key = "", language="English",tone="normal",headings=5,length="very long",main_prompt=None, prd_base_prompt=None,slug_prompt=None,title_prompt=None,conclusion_prompt=None,body_prompt=None,headings_prompt=None, image_prompt=None,heading_image_prompt=None,product_blog=False,referral_id=None,product_prompt=None,product_link=None, product_image_link=None):
    openai.api_key = openai_key
    
    product_template = '<div class="aawp"><div class="aawp-product aawp-product--horizontal aawp-product--css-adjust-image-large" data-aawp-product-asin="PRODUCT_CODE" data-aawp-product-id="" data-aawp-tracking-id="" data-aawp-product-title="PRODUCT_NAME"><div class="aawp-product__thumb" style="width:100%;"><a class="aawp-product__image-link" href="PRODUCT_LINK" title="PRODUCT_NAME" rel="nofollow noopener sponsored" target="_blank"><img decoding="async" class="aawp-product__image" src="PRODUCT_IMAGE" alt="PRODUCT_NAME"></a></div><div> <div style="padding:10px !important" class="aawp-product__content"><a class="aawp-product__title" href="PRODUCT_LINK" title="PRODUCT_NAME" rel="nofollow noopener sponsored" target="_blank">PRODUCT_NAME </a><div class="aawp-product__description"><p></p><p>PRODUCT_DESC</p><p> </p></div></div><div style="margin-left: 10px !important" class="aawp-product__footer"><div class="aawp-product__pricing"><a href="PRODUCT_LINK" title="Amazon Prime" rel="nofollow noopener sponsored" target="_blank" class="aawp-check-prime"><img decoding="async" src="https://samples.koala.sh/wp-content/plugins/aawp/assets/img/icon-check-prime.svg" alt="Amazon Prime"></a> </div> <div style="margin-top:10px !important"> <a class="aawp-button aawp-button--buy aawp-button aawp-button--amazon rounded aawp-button--icon aawp-button--icon-amazon-black" href="PRODUCT_LINK" title="Check Price on Amazon" target="_blank" rel="nofollow noopener sponsored">Check Price on Amazon</a> </div></div> </div></div></div>'
    final_article = '<html><head><style>.aawp-product { display: flex;        border: 1px solid #e2e2e2;        border-radius: 15px;        overflow: hidden;    }    .aawp .aawp-product--horizontal.aawp-product--sale {        border-color: #27ae60;    }    .aawp .aawp-product--horizontal.aawp-product--sale .aawp-product__title {        color: #27ae60;    }    .aawp .aawp-product--horizontal {        border-width: 3px;        border-color: #e8e8e8;    }    .aawp .aawp-button.aawp-button--amazon {        font-weight: 500 !important;        padding: 10px 19px !important;        padding-left: 36px !important;        background: #f0c14b !important;        border: none !important;    }    .aawp .aawp-product--horizontal .aawp-product__image {        max-height: 300px !important;        margin: 0;    }    .aawp .aawp-button.aawp-button--icon:before, .aawp-button.aawp-button--icon:before {background-position: 13px calc(50% + 1px);    }</style></head><body>'
    slug = ""
    
    # re-write conent
    base_prompt =""
    if prd_base_prompt is not None:
        prd_base_prompt = str(prd_base_prompt).replace("{headings}",headings).replace("{language}",language).replace("{tone}",tone).replace("{length}",length)
        base_prompt = prd_base_prompt
    elif product_blog == True and product_prompt is not None:
        base_prompt = product_prompt.replace("{product}", main_prompt)
    else:
        base_prompt = f"You should act as a highly professional {language} blog writer, you would be given article text as input and YOU SHOULD using your own knowledge of that domain discussed in the input text write {length} content as detailed as possible in {tone} tone and return correctly formatted html response in {language} language"

    if main_prompt is not None and product_blog == False:
        base_prompt = base_prompt + " " + main_prompt
    head_prompt = f"Considering the provided summary of a article please return a stable diffusion prompt that will generate suitable image for blog. Summary: {summary}"
    if heading_image_prompt is not None and heading_image_prompt != "" and product_blog == False:
        head_prompt = str(heading_image_prompt).replace("{text}",text)
    
    chatmessages = [{"role":"system", "content":base_prompt}]
    
    #get generated article title
    tl_prompt = ""
    if product_blog == True:
        tl_prompt = f"Considering the product {main_prompt} please write one liner text title in {language} and it should be SEO friendly without having any html tag"
    else:    
        tl_prompt = f"Rewrite the article title {title} in {language} with h1 tag and it should be SEO friendly" if title_prompt is None else str(title_prompt).replace("{context}",title)    
    chatmessages.append({"role":"user","content":tl_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    
    chatmessages.append(output.choices[0].message)
    final_article = final_article + "<h1>" + str(output.choices[0].message.content).strip('"') + "</h1> </br>"
    
    regen_title = output.choices[0].message.content
    regen_title = str(regen_title).strip('"')
    
    
    # get product description it its a product blog
    product_description = ""
    if product_blog == True:
        chatmessages.append({"role":"user","content":f"Considering the product {main_prompt} please provide one line text description about it"})
        output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
        product_description =  output.choices[0].message.content
    #generate main heading image if its not a product blog
    image_head = ""
    if product_blog == False:
        chatmessages.append({"role":"user","content":head_prompt})
        output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
        sd_gen_prompt = output.choices[0].message.content
        
        image_head = await gen_image_from_prompt(sd_gen_prompt,stable_diff_key)
    else:
        image_head = await gen_image_from_image_for_product("You should provide an attractive variation of this product image with a phenominal background such that this product should become eye catching for the buyer",product_image_link,stable_diff_key)
    preview_image_url=""
    
    if image_head is not None and image_head != "":
        preview_image_url = image_head
        final_article = final_article + f'<img src="{image_head}" /> </br>'
    else: 
        heading_image = ""
        img_prmpt = "Regenrate this image in HQ 4K but it should not look exactly like this" if image_prompt is None else image_prompt
        if len(images) > 0:
            
            heading_image = await gen_image_from_image(img_prmpt, images[0],stable_diff_key)
            
            preview_image_url = heading_image
            final_article = final_article + f'</br> <img src="{heading_image}"/> </br>'
    
    #get 5 headings considering the article text
    hd_prompt = ""
    if product_blog == True:
        hd_prompt = f"Considering the product {main_prompt} return {headings} sub headings for blog and make sure first one should be an introductory heading and response should be an array which can be parsed through json parsing for example ['Intro heading','heading2','heading3','heading4','heading5']"
    else:
        hd_prompt = f"Considering this article text {text} return {headings} sub headings for blog and make sure first one should be an introductory heading and response should be an array which can be parsed through json parsing for example ['Intro heading','heading2','heading3','heading4','heading5']" if headings_prompt is None else f"Considering this article text {text} "+ headings_prompt
    chatmessages.append({"role":"user","content":hd_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    
    #considering it should be returning an array
    sub_headings_arrays = json.loads(output.choices[0].message.content)
    
    count = 1
    await asyncio.sleep(60)
    for sub_heads in sub_headings_arrays:
        bdy_prompt = f"For the sub heading {sub_heads} write 3 very long and detailed paragraph in {language} and return response as valid html format" if body_prompt is None else str(body_prompt).replace("{subhead}",sub_heads)
        chatmessages.append({"role":"user","content":bdy_prompt})
        output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
        del chatmessages[-1]
        #chatmessages.append(output.choices[0].message)
        final_article = final_article + output.choices[0].message.content
        
        if len(images) >= count + 1:
            #then there exist image for headings
            img_prmpt = "Regenrate this image in HQ 4K but it should not look exactly like this" if image_prompt is None else image_prompt
            sub_heading_image = await gen_image_from_image(img_prmpt, images[count],stable_diff_key)
            if sub_heading_image is not None:
                final_article = final_article + f'</br> <img src="{sub_heading_image}"/> '
            count=count+1
    #generate conclusion 
    
    await asyncio.sleep(60)
    cnc_prompt = ""
    if product_blog == True:
        cnc_prompt = f"Considering the product {main_prompt} write a very long and detailed conclusion paragraph in {language} and return response as valid html format"
    else:
        cnc_prompt = f"Check this summary of the article: {summary} write a very long and detailed conclusion paragraph in {language} and return response as valid html format" if conclusion_prompt is None else f"Check this summary of the article: {summary} " + conclusion_prompt
    chatmessages.append({"role":"user","content":cnc_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    final_article = final_article + output.choices[0].message.content
    if len(images) > count:
        #then there exist image for conclusion
        sub_heading_image = await gen_image_from_image(img_prmpt, images[count],stable_diff_key)
        if sub_heading_image is not None:
            final_article = final_article + f"</br> <img src='{sub_heading_image}'/>"
    slg_prompt = f"For this article create a unique SEO optimized slug as well but return in plain text English with hyphen as separator of words" if slug_prompt is None else slug_prompt
    chatmessages.append({"role":"user","content":slg_prompt})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    slug = output.choices[0].message.content
    
    if product_blog == True:
        product_code = ""
        is_slash = False
        if product_link[len(product_link)-1] == '/':
            is_slash = True
            product_link = product_link[:-1]
            product_code = str(product_link).split('/')[len(str(product_link).split('/'))-1]
        else:
            product_code = str(product_link).split('/')[len(str(product_link).split('/'))-1]
        product_card = product_template.replace("PRODUCT_LINK",product_link+"/ref=nosim?tag="+referral_id).replace("PRODUCT_CODE",product_code).replace("PRODUCT_NAME",regen_title).replace("PRODUCT_DESC",product_description).replace("PRODUCT_IMAGE",product_image_link)
        final_article = final_article +"</br>" + product_card

    final_article = final_article +"</br></body></html>"
    return {"article": final_article, "title": regen_title, "slug": slug, "image": preview_image_url}

async def gen_image_from_image(prompt,image_url,key):
    try:
        url = "https://stablediffusionapi.com/api/v1/enterprise/img2img"
        payload = json.dumps({
        "key": key,
        "prompt": prompt,
        "model_id": os.getenv("SD_MODEL","midjourney"),
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
        "model_id": os.getenv("SD_MODEL","midjourney"),
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
        if len(response.get("output")) !=  0:
             return response.get("output")[0]
        
        if len(response.get("image_links")) != 0:
            return response.get("image_links")[0]
        
        return None
    except Exception as err:
        print(err)
        return None
    
async def gen_image_from_image_for_product(prompt,image_url,key):
    try:
        url = "https://stablediffusionapi.com/api/v1/enterprise/img2img"
        payload = json.dumps({
        "key": key,
        "prompt": prompt,
        "model_id": os.getenv("SD_MODEL","midjourney"),
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
        if len(response.get("output")) !=  0:
             return response.get("output")[0]
        
        if len(response.get("image_links")) != 0:
            return response.get("image_links")[0]
    except Exception as err:
        print(err)
        return ""