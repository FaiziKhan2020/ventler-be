import openai
import requests
import json

async def gpt_rewrite(title,text,summary, openai_key, user_prompt = None, images = []):
    openai.api_key = openai_key
    final_article = ""
    # re-write conent
    base_prompt = "You should act as a highly professional Korean blog writer, you would be given article text as input and YOU SHOULD using your own knowledge of that domain discussed in the input text write a large content as detailed as possible and return correctly formatted html response"
    if user_prompt is not None:
        if user_prompt != "":
            base_prompt = base_prompt + user_prompt
    chatmessages = [{"role":"system", "content":base_prompt}]
    #get generated article title
    chatmessages.append({"role":"user","content":f"Rewrite the article title {title} in KOREAN with h1 tag and it should be SEO friendly"})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    final_article = final_article + output.choices[0].message.content
    regen_title = output.choices[0].message.content
    heading_image = ""
    if len(images) > 0:
        print(images[0])
        heading_image = gen_image_from_image("Regenrate this image in HQ 4K but it should not look exactly like this", images[0])
        final_article = final_article + f"</br> <img src='{heading_image}'/> </br> </br>"
    
    #get 5 headings considering the article text
    chatmessages.append({"role":"user","content":f"Considering this article text {text} return 5 sub headings for blog and make sure first one should be an introductory heading and response should be an array which can be parsed through json parsing for example ['Intro heading','heading2','heading3','heading4','heading5']"})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    #considering it should be returning an array
    sub_headings_arrays = json.loads(output.choices[0].message.content)
    count = 1
    for sub_heads in sub_headings_arrays:
        chatmessages.append({"role":"user","content":f"For the sub heading {sub_heads} write 3 very long and detailed paragraph in KOREAN and return response as valid html format"})
        output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
        chatmessages.append(output.choices[0].message)
        final_article = final_article + output.choices[0].message.content
        if len(images) >= count + 1:
            #then there exist image for headings
            sub_heading_image = gen_image_from_image("Regenerate this image in HQ 4K but it should not look exactly like this", images[count])
            final_article = final_article + f"</br> <img src='{sub_heading_image}'/> </br> </br>"
            count=count+1
    #generate conclusion 
    chatmessages.append({"role":"user","content":f"Check this summary of the article: {summary} write a very long and detailed conclusion paragraph in KOREAN and return response as valid html format"})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    final_article = final_article + output.choices[0].message.content
    if len(images) >= count:
        #then there exist image for conclusion
        sub_heading_image = gen_image_from_image("Regenerate this image in HQ 4K but it should not look exactly like this", images[count])
        final_article = final_article + f"</br> <img src='{sub_heading_image}'/> </br> </br>"
    return {"article": final_article, "title": regen_title}

async def gen_image_from_image(prompt,image_url):
    url = "https://stablediffusionapi.com/api/v3/img2img"
    payload = json.dumps({
    "key": "",
    "prompt": prompt,
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
    return response.json().output[0]